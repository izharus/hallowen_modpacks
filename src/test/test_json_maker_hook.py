"""Tests for src/json_maker_hook.py"""
# pylint:disable = E0401, R0123, C0411
import hashlib
import json
import os
from unittest.mock import MagicMock

import json_maker_hook
import pytest
from src.pydantic_models import FileInfo, MapJson, ServerConfig


def test_incorrect_hash_value_from_calculate_hash(tmpdir):
    """Test if calculate_hash() calculates incorrect hashes"""
    file_content = b"Hello, World!"
    file_path = tmpdir.join("test_file.txt")
    file_path.write(file_content)

    hash_value = json_maker_hook.calculate_hash(file_path, "sha256")
    expected_hash = hashlib.sha256(file_content).hexdigest()

    assert hash_value == expected_hash


def test_calculate_hash_not_raises_error(tmpdir):
    """Test if calculate_hash() handles non-existent files."""
    non_existent_file = tmpdir.join("non_existent_file.txt")

    with pytest.raises(json_maker_hook.CalculateHashFailed):
        json_maker_hook.calculate_hash(non_existent_file, "sha256")


def test_calculate_hash_uses_invalid_algorithm(tmpdir):
    """Test if calculate_hash() handles invalid hash algorithms."""
    file_content = b"Hello, World!"
    file_path = tmpdir.join("test_file.txt")
    file_path.write(file_content)

    with pytest.raises(json_maker_hook.CalculateHashFailed):
        json_maker_hook.calculate_hash(file_path, "invalid_algorithm")


def test_generate_file_absolute_path(tmpdir):
    """Test the generate_file_info() with absolute path."""

    abs_path = str(tmpdir)
    base_api_url = "https://example.com/api/"
    with pytest.raises(ValueError):
        json_maker_hook.generate_file_info(
            abs_path,
            base_api_url,
        )


def test_generate_file_generates_two_files(tmpdir):
    """Test the generate_file_info() function."""
    # Create a temporary directory for testing
    relative_path = "test_modpacks"
    modpacks_directory = tmpdir.mkdir(relative_path)
    original_path = os.getcwd()
    try:
        base_api_url = "https://example.com/api/"
        filename1 = "file1.txt"
        file1_content = b"File 1 content"

        filename2 = "file2.txt"
        file2_content = b"File 2 content"
        file2_subdir = "subdirectory"
        # Create some test files in the temporary directory
        file1 = modpacks_directory.join(filename1)
        file1.write(file1_content)
        file2 = modpacks_directory.mkdir(file2_subdir).join(filename2)
        file2.write(file2_content)

        os.chdir(tmpdir)
        # Generate file information
        file_info_list = json_maker_hook.generate_file_info(
            relative_path,
            base_api_url,
        )

        assert file_info_list[0].file_name == filename1
        assert (
            file_info_list[0].api_url
            == f"{base_api_url}{relative_path}/{filename1}"
        )
        assert (
            file_info_list[0].yan_obj_storage == f"{relative_path}/{filename1}"
        )
        assert (
            file_info_list[0].hash == hashlib.sha256(file1_content).hexdigest()
        )
        assert file_info_list[0].dist_file_path == filename1

        assert file_info_list[1].file_name == filename2
        assert (
            file_info_list[1].api_url
            == f"{base_api_url}{relative_path}/{file2_subdir}/{filename2}"
        )
        assert (
            file_info_list[1].yan_obj_storage
            == f"{relative_path}/{file2_subdir}/{filename2}"
        )
        assert (
            file_info_list[1].hash == hashlib.sha256(file2_content).hexdigest()
        )
        assert file_info_list[1].dist_file_path == os.path.join(
            file2_subdir,
            filename2,
        )

    finally:
        os.chdir(original_path)


def test_generate_file_info_should_return_empty_list_for_empty_dir(tmpdir):
    """Test generate_file_info() with an empty directory."""
    # Create an empty directory for testing
    relative_path = "test_modpacks"
    tmpdir.mkdir(relative_path)
    original_path = os.getcwd()
    try:
        base_api_url = "https://example.com/api/"

        os.chdir(tmpdir)
        # Generate file information for an empty directory
        file_info = json_maker_hook.generate_file_info(
            relative_path,
            base_api_url,
        )

        # The result should be an empty list
        assert not file_info
    finally:
        os.chdir(original_path)


def test_generate_json_success(tmpdir, mocker):
    """Test the generate_json() function."""
    # Create a temporary directory for testing
    relative_path = "test_modpacks"
    modpacks_directory = tmpdir.mkdir(relative_path)
    original_path = os.getcwd()
    try:
        os.chdir(tmpdir)
        base_api_url = "https://example.com/api/"

        # Create subdirectories and files within the "modpacks" directory
        modpack1_name = "modpack1"
        modpack1 = modpacks_directory.mkdir(modpack1_name)
        modpack1.mkdir("main_data").join("file1.txt").write("File 1 content")
        modpack1.mkdir("client_additional_data").mkdir("some_content").join(
            "file3.txt"
        ).write("File additional content")
        main_data1 = json_maker_hook.generate_file_info(
            os.path.join(
                relative_path,
                modpack1_name,
                "main_data",
            ),
            base_api_url,
        )
        client_additional_data1 = {
            "some_content": json_maker_hook.generate_file_info(
                os.path.join(
                    relative_path,
                    modpack1_name,
                    "client_additional_data",
                    "some_content",
                ),
                base_api_url,
            )
        }
        modpack2_name = "modpack2"
        modpack2 = modpacks_directory.mkdir(modpack2_name)
        modpack2.mkdir("main_data").join("file4.txt").write("File 4 content")
        client_additional_data2 = {}
        main_data2 = json_maker_hook.generate_file_info(
            os.path.join(
                relative_path,
                modpack2_name,
                "main_data",
            ),
            base_api_url,
        )
        with mocker.patch.object(
            json_maker_hook,
            "parse_config_dict",
            return_value=MagicMock(spec=json_maker_hook.ServerConfig),
        ):
            os.chdir(tmpdir)
            # Execute the generate_json function with
            # the specified JSON file path
            map_json = json_maker_hook.generate_json(
                relative_path, base_api_url
            )
        assert len(map_json.modpacks) == 2

        # pylint: disable=C0301
        assert map_json.modpacks[modpack1_name].main_data == main_data1
        assert (
            map_json.modpacks[modpack1_name].client_additional_data
            == client_additional_data1
        )
        assert map_json.modpacks[modpack2_name].main_data == main_data2
        assert (
            map_json.modpacks[modpack2_name].client_additional_data
            == client_additional_data2
        )
    finally:
        os.chdir(original_path)


def test_generate_json_returns_non_empty_data_for_empty_dir(tmpdir):
    """Test generate_json() with an empty directory."""
    # Create an empty "modpacks" directory for testing
    modpacks_directory = tmpdir.mkdir("modpacks")
    base_api_url = "https://example.com/api/"

    # Execute the generate_json function with an empty directory
    map_json = json_maker_hook.generate_json(
        str(modpacks_directory), base_api_url
    )
    assert map_json.modpacks == {}


def test_generate_json_return_nonexistent_directory(tmpdir):
    """Test generate_json() with a non-existent directory."""
    # Specify a non-existent directory for testing
    non_existent_directory = os.path.join(str(tmpdir), "non_existent_modpacks")
    base_api_url = "https://example.com/api/"

    # Execute the generate_json function with a non-existent directory
    map_json = json_maker_hook.generate_json(
        non_existent_directory, base_api_url
    )
    assert map_json.modpacks == {}


def test_parse_config_dict_valid_config(tmpdir):
    """Test parse_config_dict with valid file."""
    config_file = tmpdir.join("config.json")
    valid_config = {
        "config_name": "terrafirmacraf//t_test",
        "minecraft_version": "1.18.2",
        "forge_version": "1.18.2-40.2.9",
        "minecraft_profile": "1.18.2-forge-40.2.9",
        "minecraft_server_ip": "77.239.232.50",
        "minecraft_server_port": "25570",
    }

    with config_file.open("w") as f:
        json.dump(valid_config, f)

    res_config = json_maker_hook.parse_config_dict(config_file.strpath)
    assert ServerConfig(**valid_config) == res_config


def test_parse_config_dict_invalid_config(tmpdir):
    """Test parse_config_dict with invalid file."""
    config_file = tmpdir.join("config.json")
    valid_dict = {
        "config_name": 1,  # here should be str name
        "minecraft_version": "1.18.2",
        "forge_version": "1.18.2-40.2.9",
        "minecraft_profile": "1.18.2-forge-40.2.9",
        "minecraft_server_ip": "77.239.232.50",
        "minecraft_server_port": "25570",
    }

    with config_file.open("w") as f:
        json.dump(valid_dict, f)
    with pytest.raises(RuntimeError):
        json_maker_hook.parse_config_dict(str(config_file))


def test_create_github_api_url_default_usage():
    """
    Test correct creation of URL for base API URL and path
    to file in repository.
    """
    base_api_url = "https://api.github.com/repos/username/repository"
    path_to_file_in_repo = "folder/subfolder/file.txt"
    # pylint: disable=C0301
    expected_url = "https://api.github.com/repos/username/repository/folder/subfolder/file.txt"
    assert (
        json_maker_hook.create_github_api_url(
            base_api_url, path_to_file_in_repo
        )
        == expected_url
    )


def test_create_github_api_url_with_windows_path():
    """
    Test creation of URL with replacing backslashes with forward slashes.
    """
    base_api_url = "https://api.github.com/repos/username/repository"
    path_to_file_in_repo = "folder\\subfolder\\file.txt"
    # pylint: disable=C0301
    expected_url = "https://api.github.com/repos/username/repository/folder/subfolder/file.txt"
    assert (
        json_maker_hook.create_github_api_url(
            base_api_url, path_to_file_in_repo
        )
        == expected_url
    )


def test_create_github_api_url_with_trailing_slash():
    """
    Test creation of URL when base API URL ends with "/".
    """
    base_api_url = "https://api.github.com/repos/username/repository/"
    path_to_file_in_repo = "folder/subfolder/file.txt"
    # pylint: disable=C0301
    expected_url = "https://api.github.com/repos/username/repository/folder/subfolder/file.txt"
    assert (
        json_maker_hook.create_github_api_url(
            base_api_url, path_to_file_in_repo
        )
        == expected_url
    )


def test_create_github_api_url_with_null_base_url():
    """
    Test creation of URL when base API URL is null.
    """
    base_api_url = "invalid_url"
    path_to_file_in_repo = "folder/subfolder/file.txt"
    with pytest.raises(ValueError):
        json_maker_hook.create_github_api_url(
            base_api_url, path_to_file_in_repo
        )


def test_create_github_api_url_empty_path():
    """
    Test that ValueError is raised when an empty path to file
    in repository is provided.
    """
    # Define a valid base API URL
    base_api_url = "https://api.github.com/"

    # Define an empty path to file in repo
    path_to_file_in_repo = ""

    # Check that ValueError is raised with appropriate error message
    with pytest.raises(ValueError) as exc_info:
        json_maker_hook.create_github_api_url(
            base_api_url, path_to_file_in_repo
        )

    assert (
        str(exc_info.value) == "Path to file in repository could not be empty"
    )


def test_get_all_obj_keys_empty_map_json():
    """Test get_all_obj_keys with an empty map_json."""
    map_json = MapJson(modpacks={})
    # pylint: disable=C1803
    assert json_maker_hook.get_all_obj_keys(map_json) == {}


def test_get_all_obj_keys_single_modpack_single_dir():
    """Test get_all_obj_keys with a single modpack and a single directory."""
    mock_file_info1 = MagicMock(spec=FileInfo)
    mock_file_info1.yan_obj_storage = "obj_key_1"
    mock_file_info1.hash = "hash_value_1"
    mock_file_info2 = MagicMock(spec=FileInfo)
    mock_file_info2.yan_obj_storage = "obj_key_2"
    mock_file_info2.hash = "hash_value_2"
    map_json = MapJson(
        modpacks={
            "modpack_1": {
                "main_data": [
                    mock_file_info1,
                    mock_file_info2,
                ],
                "server_config": MagicMock(spec=ServerConfig),
                "client_additional_data": {},
            }
        }
    )
    expected_result = {
        "obj_key_1": "hash_value_1",
        "obj_key_2": "hash_value_2",
    }
    assert json_maker_hook.get_all_obj_keys(map_json) == expected_result


def test_get_all_obj_keys_multiple_modpacks_multiple_dirs(mocker):
    """
    Test get_all_obj_keys with multiple modpacks and multiple directories.
    """
    mock_file_info1 = MagicMock(spec=FileInfo)
    mock_file_info1.yan_obj_storage = "obj_key_1"
    mock_file_info1.hash = "hash_value_1"
    mock_file_info2 = MagicMock(spec=FileInfo)
    mock_file_info2.yan_obj_storage = "obj_key_2"
    mock_file_info2.hash = "hash_value_2"
    mock_file_info3 = MagicMock(spec=FileInfo)
    mock_file_info3.yan_obj_storage = "obj_key_3"
    mock_file_info3.hash = "hash_value_3"
    mock_file_info4 = MagicMock(spec=FileInfo)
    mock_file_info4.yan_obj_storage = "obj_key_4"
    mock_file_info4.hash = "hash_value_4"

    mocker.patch.object(json_maker_hook, "ServerConfig", spec=True)

    map_json = MapJson(
        modpacks={
            "modpack_1": {
                "main_data": [
                    mock_file_info1,
                    mock_file_info2,
                ],
                "server_config": json_maker_hook.ServerConfig(),
                "client_additional_data": {},
            },
            "modpack_2": {
                "main_data": [],
                "client_additional_data": {
                    "shaders_data": [mock_file_info3],
                    "some_other_additional_data": [mock_file_info4],
                },
                "server_config": json_maker_hook.ServerConfig(),
            },
        }
    )

    expected_result = {
        "obj_key_1": "hash_value_1",
        "obj_key_2": "hash_value_2",
        "obj_key_3": "hash_value_3",
        "obj_key_4": "hash_value_4",
    }
    assert json_maker_hook.get_all_obj_keys(map_json) == expected_result
