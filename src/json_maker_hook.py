"""
`json_maker_hook.py` is a script for generating a JSON representation of
modpack data used in Minecraft. It supports multiple servers and
modpacks, collecting information about different modpacks, including
'main_data', 'client_data', and 'server_data.'

This script calculates the hash of files, generates information about files
in a directory, and creates a JSON representation of modpack data for
a Minecraft repository.
"""
import hashlib
import json
import os
import sys
from typing import Dict, Iterable, List
from urllib.parse import urljoin

import boto3
import jsonschema
import validators
from loguru import logger as log

from .pydantic_models import ConfigJson, FileInfo, MapJson, Modpack

log.add(
    "data/logs/file_{time:YYYY-MM}.log",
    rotation="1 month",
    retention="1 month",  # Retain log files for 1 month after rotation
    compression="zip",  # Optional: Enable compression for rotated logs
    level="DEBUG",
    serialize=False,
)

ACCESS_KEY = "YCAJExAnweRt_N7-ZgPopPA71"
SECRET_KEY = os.environ.get("YANDEX_OBJECT_STORAGE_EDITOR_KEY")
REGION_NAME = "ru-central1"  # Укажите ваш регион Yandex Object Storage
BUCKET_NAME = "tfc.halloween"
# pylint: disable = C0301
REPOSITORY_API_URL = (
    "https://raw.githubusercontent.com/izharus/hallowen_modpacks/dev/"
)
PATH_TO_MODPACKS_DIR = "modpacks"

# Ваш JSON Schema
SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "config_name": {"type": "string"},
        "minecraft_version": {"type": "string"},
        "forge_version": {"type": "string"},
        "minecraft_profile": {"type": "string"},
        "minecraft_server_ip": {"type": "string", "format": "ipv4"},
        "minecraft_server_port": {"type": "string", "pattern": "^\\d{1,5}$"},
    },
    "required": [
        "config_name",
        "minecraft_version",
        "forge_version",
        "minecraft_profile",
        "minecraft_server_ip",
        "minecraft_server_port",
    ],
}


class CalculateHashFailed(RuntimeError):
    """Raises if calculate_hash func raises any exception."""

    def __init__(self, message="Calculate_hash function failed.") -> None:
        super().__init__(message)


def calculate_hash(file_name, hash_algorithm="sha256"):
    """Calculate the hash of a file using the specified hash algorithm."""
    try:
        # Create a hash object based on the specified algorithm
        hasher = hashlib.new(hash_algorithm)

        # Open the file in binary mode for reading
        with open(file_name, "rb") as file:
            while True:
                # Read the file in small chunks to conserve memory
                chunk = file.read(4096)
                if not chunk:
                    break
                hasher.update(chunk)

        # Return the hexadecimal representation of the hash
        return hasher.hexdigest()
    except Exception as error:
        raise CalculateHashFailed() from error


def parse_config_dict(config_path: str) -> ConfigJson:
    """
    Parse a configuration file located at the specified path.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        ConfigJson: A ConfigJson instance containing the parsed
            configuration data.

    Raises:
        RuntimeError: If there is an error parsing the config file or
            if the validation fails.
    """
    try:
        with open(config_path, encoding="utf-8") as fr:
            config_data = json.load(fr)
    except Exception as error:
        raise RuntimeError(f"unable to parse config file: {error}") from error
    # Exception will be raised if json structure incorrect
    try:
        jsonschema.validate(instance=config_data, schema=SCHEMA)
    except jsonschema.exceptions.ValidationError as error:
        raise RuntimeError(
            f"validation of config file failed: {error}"
        ) from error
    return ConfigJson(**config_data)


def create_github_api_url(base_api_url: str, path_to_file_in_repo: str) -> str:
    """
    Create a GitHub API URL by joining the base API URL with the path
    to the file in the repository.

    Args:
        base_api_url (str): The base URL of the GitHub API.
        path_to_file_in_repo (str): The path to the file within the repository.

    Returns:
        str: The constructed GitHub API URL.

    Raises:
        ValueError: If the base_api_url is not a valid URL
            or if path_to_file_in_repo is empty.
    """
    # Validate base API URL
    if not validators.url(base_api_url):
        raise ValueError("Invalid base API URL")
    # Validate path to file in repo
    if not path_to_file_in_repo:
        raise ValueError("Path to file in repository could not be empty")
    # Normalize base API URL by ensuring it ends with a trailing slash
    base_api_url = base_api_url.rstrip("/") + "/"

    # Replace backslashes with forward slashes in the path
    normalized_path = path_to_file_in_repo.replace("\\", "/")

    # Construct the complete URL
    return urljoin(base_api_url, normalized_path)


def generate_file_info(
    root_directory: str,
    base_api_url: str,
) -> List[FileInfo]:
    """
    Generate information about files in a directory.

    Args:
        root_directory (str): The root directory to search
            for files. Path should be relative.
        base_api_url (str): The base URL for the API where the files
            can be downloaded.

    Returns:
        List[dict]: A list of dictionaries containing information about the
            files found in the directory.

    Each dictionary contains the following keys:
    - 'file_name': The name of the file.
    - 'api_url': The URL where the file can be downloaded.
        api_url = base_api_url + relative path (where
        the root_directory is a base path).
    - 'hash': The hash value of the file.
    - 'dist_file_path': The relative path of the file. Into this path
        file should be downloaded.
    """
    if os.path.isabs(root_directory):
        raise ValueError("Path should be relative")
    map_files = []
    for root, _directories, files in os.walk(root_directory):
        for file_name in files:
            relative_file_path = os.path.join(root, file_name)
            dist_file_path = os.path.relpath(
                os.path.join(root, file_name),
                root_directory,
            )
            download_api_url = create_github_api_url(
                base_api_url,
                relative_file_path,
            )
            map_files.append(
                FileInfo(
                    **{
                        "file_name": file_name,
                        "api_url": download_api_url,
                        "yan_obj_storage": relative_file_path.replace(
                            "\\", "/"
                        ),
                        "hash": calculate_hash(relative_file_path),
                        "dist_file_path": dist_file_path,
                    }
                )
            )
    return map_files


def generate_json(relative_path: str, repository_api_url: str) -> MapJson:
    """
    Generate a MapJson object representation of modpack data.

    Parameters:
        relative_path (str): The relative path to the directory
            containing modpack data.
        repository_api_url (str): The URL to the repository where modpack
            data is hosted.

    Returns:
        MapJson: A MapJson instance containing information about modpacks.
    """
    # pylint: disable = C0301
    map_json: Dict = {}
    for root, directories, _ in os.walk(relative_path):
        if root == relative_path:
            for modpack_name in directories:
                map_json[modpack_name] = {}
                config_path = os.path.join(root, modpack_name, "config.json")
                config = parse_config_dict(config_path)

                main_data = generate_file_info(
                    os.path.join(root, modpack_name, "main_data"),
                    repository_api_url,
                )

                additional_data_path = os.path.join(
                    root, modpack_name, "client_additional_data"
                )
                client_additional_data = {}
                os.makedirs(additional_data_path, exist_ok=True)
                for dir_name in os.listdir(additional_data_path):
                    client_additional_data[dir_name] = generate_file_info(
                        os.path.join(
                            root,
                            modpack_name,
                            "client_additional_data",
                            dir_name,
                        ),
                        repository_api_url,
                    )
                map_json[modpack_name] = Modpack(
                    config=config,
                    main_data=main_data,
                    client_additional_data=client_additional_data,
                )
    return MapJson(modpacks=map_json)


def get_all_obj_keys(map_json: MapJson) -> Dict:
    """
    Get all object keys from the provided map_json.

    Args:
        map_json (Dict): A dictionary containing information about object keys.

    Returns:
        Dict: A dictionary containing all object keys.

    Notes:
        The function returns a dictionary where the keys are 'yan_obj_storage'
        values and the values are 'hash' values.
    """
    res = {}
    for _, modpack_data in map_json.modpacks.items():
        res.update(
            {
                file_info.yan_obj_storage: file_info.hash
                for file_info in modpack_data.main_data
            }
        )
        for _, additional_data in modpack_data.client_additional_data.items():
            res.update(
                {
                    file_info.yan_obj_storage: file_info.hash
                    for file_info in additional_data
                }
            )
    return res


def delete_files(
    boto3_client: boto3.client,
    bucket_name: str,
    obj_keys: Iterable[str],
) -> None:
    """
    Delete multiple objects from an S3 bucket.

    Args:
        boto3_client (boto3.client): Boto3 S3 client.
        bucket_name (str): Name of the S3 bucket.
        obj_keys (Iterable[str]): List of object keys (file paths) to delete.

    Raises:
        botocore.exceptions.ClientError: If any error occurs
            during object deletion.
    """
    for obj_key in obj_keys:
        log.info(f"Deleting: {obj_key}")
        boto3_client.delete_object(Bucket=bucket_name, Key=obj_key)


def upload_new_files(
    boto3_client: boto3.client,
    bucket_name: str,
    old_object_keys: Dict[str, str],
    new_object_keys: Dict[str, str],
):
    """
    Upload new or modified files to an S3 bucket.

    Args:
        boto3_client (boto3.client): Boto3 S3 client.
        bucket_name (str): Name of the S3 bucket.
        old_object_keys (Dict[str, str]): Dictionary containing old
            object keys and hashes.
        new_object_keys (Dict[str, str]): Dictionary containing new
            object keys and hashes.

    Raises:
        IOError: If an I/O error occurs during file operation.
        botocore.exceptions.ClientError: If an error occurs during file upload.
            This includes errors such as FileNotFoundError
            (if the file specified by the object key does not exist),
            AccessDenied (if access is denied), etc.
    """
    for object_key, new_file_hash in new_object_keys.items():
        old_file_hash = old_object_keys.get(object_key, "None")
        if old_file_hash != new_file_hash:
            log.info(
                f"Uploading: {object_key}, old/new hash: "
                f"{old_file_hash}/{new_file_hash}"
            )
            boto3_client.upload_file(object_key, bucket_name, object_key)


def main():
    """Main work."""
    try:
        with open("map.json", encoding="utf-8") as fr:
            map_json_old = json.load(fr)
    except FileNotFoundError:
        map_json_old = {"modpacks": {}}

    map_json_old = MapJson(**map_json_old)

    new_map_json = generate_json(PATH_TO_MODPACKS_DIR, REPOSITORY_API_URL)
    # validate map
    # MapJson(modpacks=new_map_json)
    s3 = boto3.client(
        "s3",
        endpoint_url="https://storage.yandexcloud.net",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    new_object_keys = get_all_obj_keys(new_map_json)
    old_object_keys = get_all_obj_keys(map_json_old)

    set_old_hashes = set(old_object_keys.keys())
    set_new_hashes = set(new_object_keys.keys())

    # delete all old files
    delete_files(s3, BUCKET_NAME, set_old_hashes - set_new_hashes)

    # upload all new files
    upload_new_files(s3, BUCKET_NAME, old_object_keys, new_object_keys)

    if new_map_json != map_json_old:
        with open("map.json", "w", encoding="utf-8") as fw:
            json.dump(new_map_json.model_dump(mode="json"), fw)
        s3.upload_file(
            "map.json", BUCKET_NAME, f"{PATH_TO_MODPACKS_DIR}/map.json"
        )
        log.info("Operation success...")
        sys.exit(1)
    log.info("No any changes...")
    sys.exit(0)


if __name__ == "__main__":
    main()
