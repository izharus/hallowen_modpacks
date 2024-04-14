"""
`json_maker_hook.py` is a script for generating a JSON representation of
modpack data used in Minecraft. It supports multiple servers and
modpacks, collecting information about different modpacks, including
'main_data', 'client_data', and 'server_data.'

This script calculates the hash of files, generates information about files
in a directory, and creates a JSON representation of modpack data for
a Minecraft repository.

## Exceptions
- CalculateHashFailed: Raised if the calculate_hash function raises
    any exception.

## Functions
- calculate_hash(file_name, hash_algorithm="sha256"): Calculate the hash of a
    file using the specified hash algorithm.
- generate_file_info(...): Generate information about files in a directory.
- generate_json(...): Generate a JSON representation of modpack data.

If you plan to create additional modpacks, you can organize them in their
respective server folders and configure the `map.json` files accordingly.
This script provides flexibility for managing and distributing various
Minecraft modpacks with ease.

__Author__: [Your Name]
__License__: [License Name]
"""
import hashlib
import json
import os
import sys
from typing import Dict, List
from urllib.parse import urljoin

import jsonschema

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


def parse_config_dict(config_path: str):
    """
    Parse a configuration file located at the specified path.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: A dictionary containing the parsed configuration data.

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
    return config_data


def generate_file_info(
    root_directory: str,
    base_api_url: str,
    is_install_on_client: bool,
    is_install_on_server: bool,
) -> List[dict]:
    """
    Generate information about files in a directory.

    Args:
        root_directory (str): The root directory to search
            for files.
        base_api_url (str): The base URL for the API where the files
            can be downloaded.
        is_install_on_client (bool): Whether the files should be installed
            on the client.
        is_install_on_server (bool): Whether the files should be installed
            on the server.

    Returns:
        List[dict]: A list of dictionaries containing information about the
            files found in the directory.

    Each dictionary contains the following keys:
    - 'file_name': The name of the file.
    - 'api_url': The URL where the file can be downloaded.
        api_url = base_api_url + relative path (where
        the root_directory is a base path).
    - 'hash': The hash value of the file.
    - 'install_on_client': True if the file should be installed on
        the client, False otherwise.
    - 'install_on_server': True if the file should be installed on
        the server, False otherwise.
    - 'dist_file_path': The relative path of the file. Into this path
        file should be downloaded.
    """

    map_files = []
    for root, _directories, files in os.walk(root_directory):
        for file_name in files:
            real_file_path = os.path.join(root, file_name)
            dist_file_path = os.path.relpath(
                os.path.join(root, file_name),
                root_directory,
            )
            download_api_url = urljoin(
                urljoin(
                    base_api_url,
                    os.path.relpath(
                        root,
                        root_directory,
                    ).replace("\\", "/"),
                ),
                dist_file_path.replace("\\", "/"),
            )
            map_files.append(
                {
                    "file_name": file_name,
                    "api_url": download_api_url,
                    "hash": calculate_hash(real_file_path),
                    "install_on_client": is_install_on_client,
                    "install_on_server": is_install_on_server,
                    "dist_file_path": dist_file_path,
                }
            )
    return map_files


def generate_json(path_to_modpacks_dir: str, repository_api_url: str):
    """
    Generate a JSON representation of modpack data.

    This function walks through the 'modpacks' directory and collects
    information about different modpacks, including 'main_data',
    'client_data', and 'server_data'. The collected information is
    returned as a Python dictionary.

    Parameters:
        path_to_modpacks_dir (str): The path to the directory containing
            modpack data.
        repository_api_url (str): The URL to the repository where modpack
            data is hosted.

    Returns:
        dict: A dictionary containing information about modpacks, with
        modpack names as keys and their associated data as values. The
        data includes 'main_data', 'client_data', and 'server_data'.
    """
    # pylint: disable = C0301
    modpacks_dir_url = f"{repository_api_url}/{path_to_modpacks_dir}"
    map_json: Dict = {}
    for root, directories, _files in os.walk(path_to_modpacks_dir):
        if root == path_to_modpacks_dir:
            for modpack_name in directories:
                config_path = os.path.join(root, modpack_name, "config.json")

                main_data = generate_file_info(
                    os.path.join(root, modpack_name, "main_data"),
                    f"{modpacks_dir_url}/{modpack_name}/main_data/",
                    is_install_on_client=True,
                    is_install_on_server=True,
                )
                map_json[modpack_name] = {}
                map_json[modpack_name]["config"] = parse_config_dict(
                    config_path
                )
                map_json[modpack_name]["main_data"] = main_data
                server_data = generate_file_info(
                    os.path.join(root, modpack_name, "server_data"),
                    f"{modpacks_dir_url}/{modpack_name}/server_data/",
                    is_install_on_client=False,
                    is_install_on_server=True,
                )
                map_json[modpack_name]["server_data"] = server_data
                for dir_name in os.listdir(os.path.join(root, modpack_name)):
                    if dir_name not in ["main_data", "server_data", "config.json"]:
                        client_data = generate_file_info(
                            os.path.join(root, modpack_name, dir_name),
                            f"{modpacks_dir_url}/{modpack_name}/{dir_name}/",
                            is_install_on_client=True,
                            is_install_on_server=False,
                        )
                        map_json[modpack_name][dir_name] = client_data

    return map_json


if __name__ == "__main__":
    try:
        with open("map.json", encoding="utf-8") as fr:
            map_json_old = json.load(fr)
    except Exception:
        map_json_old = {}
    # pylint: disable = C0301
    REPOSITORY_API_URL = (
        "https://raw.githubusercontent.com/izharus/hallowen_modpacks/main/"
    )
    PATH_TO_MODPACKS_DIR = "modpacks"
    new_map_json = generate_json(PATH_TO_MODPACKS_DIR, REPOSITORY_API_URL)

    if new_map_json != map_json_old:
        with open("map.json", "w", encoding="utf-8") as fw:
            json.dump(new_map_json, fw)
        sys.exit(1)
    sys.exit(0)
