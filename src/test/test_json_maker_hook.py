"""Tests for src/json_maker_hook.py"""
# pylint:disable = E0401, R0123
import hashlib
import json
import os
from unittest.mock import MagicMock

import pytest
from src import json_maker_hook


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
            True,
            True,
        )


def test_generate_file_generates_invalid_data(tmpdir):
    """Test the generate_file_info() function."""
    # Create a temporary directory for testing
    relative_path = "test_modpacks"
    modpacks_directory = tmpdir.mkdir(relative_path)
    original_path = os.getcwd()
    try:
        base_api_url = "https://example.com/api/"
        is_install_on_client = True
        is_install_on_server = False

        # Create some test files in the temporary directory
        file1 = modpacks_directory.join("file1.txt")
        file1.write("File 1 content")
        file2 = modpacks_directory.mkdir("subdirectory").join("file2.txt")
        file2.write("File 2 content")

        os.chdir(tmpdir)
        # Generate file information
        file_info = json_maker_hook.generate_file_info(
            relative_path,
            base_api_url,
            is_install_on_client,
            is_install_on_server,
        )

        # Check the generated file information
        assert len(file_info) == 2

        # File 1
        assert file_info[0]["file_name"] == "file1.txt"
        #pylint: disable=C0301
        assert file_info[0]["api_url"] == "https://example.com/api/test_modpacks/file1.txt"
        assert file_info[0]["install_on_client"] is True
        assert file_info[0]["install_on_server"] is False
        assert "hash" in file_info[0]
        assert "dist_file_path" in file_info[0]

        # File 2
        assert file_info[1]["file_name"] == "file2.txt"
        assert (
            file_info[1]["api_url"]
            == "https://example.com/api/test_modpacks/subdirectory/file2.txt"
        )
        assert file_info[1]["install_on_client"] is True
        assert file_info[1]["install_on_server"] is False
        assert "hash" in file_info[1]
        assert "dist_file_path" in file_info[1]

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
        is_install_on_client = True
        is_install_on_server = False

        os.chdir(tmpdir)
        # Generate file information for an empty directory
        file_info = json_maker_hook.generate_file_info(
            relative_path,
            base_api_url,
            is_install_on_client,
            is_install_on_server,
        )

        # The result should be an empty list
        assert not file_info
    finally:
        os.chdir(original_path)


def test_generate_file_return_invalid_data_for_nested_files(tmpdir):
    """Test generate_file_info() with subdirectories."""
    # Create a directory structure for testing
    relative_path = "test_modpacks"
    modpacks_directory = tmpdir.mkdir(relative_path)
    original_path = os.getcwd()
    try:
        modpacks_directory.join("file1.txt").write("File 1 content")
        subdirectory = modpacks_directory.mkdir("subdirectory")
        subdirectory.join("file2.txt").write("File 2 content")

        base_api_url = "https://example.com/api/"
        is_install_on_client = True
        is_install_on_server = False

        os.chdir(tmpdir)
        # Generate file information
        file_info = json_maker_hook.generate_file_info(
            relative_path,
            base_api_url,
            is_install_on_client,
            is_install_on_server,
        )

        # Check the generated file information
        assert len(file_info) == 2

        # Check the file information for file1.txt
        assert file_info[0]["file_name"] == "file1.txt"
        assert file_info[0]["dist_file_path"] == "file1.txt"
        # pylint: disable=C0301
        assert file_info[0]["api_url"] == "https://example.com/api/test_modpacks/file1.txt"
        assert file_info[0]["install_on_client"] is True
        assert file_info[0]["install_on_server"] is False
        assert "hash" in file_info[0]
        assert "dist_file_path" in file_info[0]

        # Check the file information for file2.txt in the subdirectory
        assert file_info[1]["file_name"] == "file2.txt"
        assert file_info[1]["dist_file_path"] == "subdirectory\\file2.txt"
        assert (
            file_info[1]["api_url"]
            == "https://example.com/api/test_modpacks/subdirectory/file2.txt"
        )
        assert file_info[1]["install_on_client"] is True
        assert file_info[1]["install_on_server"] is False
        assert "hash" in file_info[1]
        assert "dist_file_path" in file_info[1]
    finally:
        os.chdir(original_path)


def test_generate_json_missing_fields(tmpdir, mocker):
    """Test the generate_json() function."""
    # Create a temporary directory for testing
    relative_path = "test_modpacks"
    modpacks_directory = tmpdir.mkdir(relative_path)
    original_path = os.getcwd()
    try:
        base_api_url = "https://example.com/api/"

        # Create subdirectories and files within the "modpacks" directory
        modpack1 = modpacks_directory.mkdir("modpack1")
        modpack1.mkdir("main_data").join("file1.txt").write("File 1 content")
        modpack1.mkdir("client_data").join("file2.txt").write("File 2 content")
        modpack1.mkdir("server_data").join("file3.txt").write("File 3 content")

        modpack2 = modpacks_directory.mkdir("modpack2")
        modpack2.mkdir("main_data").join("file4.txt").write("File 4 content")
        modpack2.mkdir("client_data").join("file5.txt").write("File 5 content")
        modpack2.mkdir("server_data").join("file6.txt").write("File 6 content")

        with mocker.patch.object(
            json_maker_hook, "parse_config_dict", MagicMock()
        ):
            os.chdir(tmpdir)
            # Execute the generate_json function with the specified JSON file path
            map_json = json_maker_hook.generate_json(
                relative_path, base_api_url
            )
        assert map_json

        assert len(map_json) == 2  # Two modpacks

        # Verify modpack1 information
        assert "modpack1" in map_json
        assert "main_data" in map_json["modpack1"]
        assert "client_data" in map_json["modpack1"]
        assert "server_data" in map_json["modpack1"]

        # Verify modpack2 information
        assert "modpack2" in map_json
        assert "main_data" in map_json["modpack2"]
        assert "client_data" in map_json["modpack2"]
        assert "server_data" in map_json["modpack2"]

    finally:
        os.chdir(original_path)


def test_generate_json_returns_non_empty_dato_for_empty_dir(tmpdir):
    """Test generate_json() with an empty directory."""
    # Create an empty "modpacks" directory for testing
    modpacks_directory = tmpdir.mkdir("modpacks")
    base_api_url = "https://example.com/api/"

    # Execute the generate_json function with an empty directory
    map_json = json_maker_hook.generate_json(
        str(modpacks_directory), base_api_url
    )

    assert not map_json


def test_generate_json_return_nonempry_dict_for_nonexistent_directory(tmpdir):
    """Test generate_json() with a non-existent directory."""
    # Specify a non-existent directory for testing
    non_existent_directory = os.path.join(str(tmpdir), "non_existent_modpacks")
    base_api_url = "https://example.com/api/"

    # Execute the generate_json function with a non-existent directory
    map_json = json_maker_hook.generate_json(
        non_existent_directory, base_api_url
    )

    # Verify that the JSON file is generated (it may be empty)
    assert not map_json


def test_generate_json_return_invalid_fields(tmpdir, mocker):
    """Test the file information structure in generate_json()."""
    # Create a temporary directory for testing
    relative_path = "test_modpacks"
    modpacks_directory = tmpdir.mkdir(relative_path)
    original_path = os.getcwd()
    try:
        base_api_url = "https://example.com/api/"

        # Create subdirectories and files within the "modpacks" directory
        modpack1 = modpacks_directory.mkdir("modpack1")
        modpack1.mkdir("main_data").join("file1.txt").write("File 1 content")
        modpack1.mkdir("client_data").join("file2.txt").write("File 2 content")
        modpack1.mkdir("server_data").join("file3.txt").write("File 3 content")

        modpack2 = modpacks_directory.mkdir("modpack2")
        modpack2.mkdir("main_data").join("file4.txt").write("File 4 content")
        modpack2.mkdir("client_data").join("file5.txt").write("File 5 content")
        modpack2.mkdir("server_data").join("file6.txt").write("File 6 content")

        with mocker.patch.object(
            json_maker_hook, "parse_config_dict", MagicMock()
        ):
            os.chdir(tmpdir)
            # Execute the generate_json function with the specified JSON file path
            map_json = json_maker_hook.generate_json(
                relative_path, base_api_url
            )

        assert map_json

        # Define the expected structure of file information
        expected_file_info_structure = {
            "file_name",
            "api_url",
            "hash",
            "install_on_client",
            "install_on_server",
            "dist_file_path",
        }
        # Check if the keys in the file_info match the expected structure
        for _modpack, info in map_json.items():
            for category_info in info.values():
                for file_info in category_info:
                    assert set(file_info.keys()) == expected_file_info_structure
    finally:
        os.chdir(original_path)


def test_parse_config_dict_valid_config(tmpdir):
    """Test parse_config_dict with valid file."""
    config_file = tmpdir.join("config.json")
    valid_dict = {
        "config_name": "terrafirmacraf//t_test",
        "minecraft_version": "1.18.2",
        "forge_version": "1.18.2-40.2.9",
        "minecraft_profile": "1.18.2-forge-40.2.9",
        "minecraft_server_ip": "77.239.232.50",
        "minecraft_server_port": "25570",
    }

    with config_file.open("w") as f:
        json.dump(valid_dict, f)

    res_dict = json_maker_hook.parse_config_dict(str(config_file))
    assert valid_dict == res_dict


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
