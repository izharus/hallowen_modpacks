"""Tests for src/json_maker_hook.py"""
# pylint:disable = E0401, R0123
import hashlib
import os

import pytest
from src.json_maker_hook import (
    CalculateHashFailed,
    calculate_hash,
    generate_file_info,
    generate_json,
)


def test_incorrect_hash_value_from_calculate_hash(tmpdir):
    """Test if calculate_hash() calculates incorrect hashes"""
    file_content = b"Hello, World!"
    file_path = tmpdir.join("test_file.txt")
    file_path.write(file_content)

    hash_value = calculate_hash(file_path, "sha256")
    expected_hash = hashlib.sha256(file_content).hexdigest()

    assert hash_value == expected_hash


def test_calculate_hash_not_raises_error(tmpdir):
    """Test if calculate_hash() handles non-existent files."""
    non_existent_file = tmpdir.join("non_existent_file.txt")

    with pytest.raises(CalculateHashFailed):
        calculate_hash(non_existent_file, "sha256")


def test_calculate_hash_uses_invalid_algorithm(tmpdir):
    """Test if calculate_hash() handles invalid hash algorithms."""
    file_content = b"Hello, World!"
    file_path = tmpdir.join("test_file.txt")
    file_path.write(file_content)

    with pytest.raises(CalculateHashFailed):
        calculate_hash(file_path, "invalid_algorithm")


def test_generate_file_generates_invalid_data(tmpdir):
    """Test the generate_file_info() function."""
    # Create a temporary directory for testing
    root_directory = tmpdir.mkdir("test_modpacks")
    base_api_url = "https://example.com/api/"
    is_install_on_client = True
    is_install_on_server = False

    # Create some test files in the temporary directory
    file1 = root_directory.join("file1.txt")
    file1.write("File 1 content")
    file2 = root_directory.mkdir("subdirectory").join("file2.txt")
    file2.write("File 2 content")

    # Generate file information
    file_info = generate_file_info(
        root_directory,
        base_api_url,
        is_install_on_client,
        is_install_on_server,
    )

    # Check the generated file information
    assert len(file_info) == 2

    # File 1
    assert file_info[0]["file_name"] == "file1.txt"
    assert file_info[0]["api_url"] == "https://example.com/api/file1.txt"
    assert file_info[0]["install_on_client"] is True
    assert file_info[0]["install_on_server"] is False
    assert "hash" in file_info[0]
    assert "dist_file_path" in file_info[0]

    # File 2
    assert file_info[1]["file_name"] == "file2.txt"
    assert (
        file_info[1]["api_url"]
        == "https://example.com/api/subdirectory/file2.txt"
    )
    assert file_info[1]["install_on_client"] is True
    assert file_info[1]["install_on_server"] is False
    assert "hash" in file_info[1]
    assert "dist_file_path" in file_info[1]

    # Add more test cases as needed


def test_generate_file_info_should_return_empty_list_for_empty_dir(tmpdir):
    """Test generate_file_info() with an empty directory."""
    # Create an empty directory for testing
    root_directory = tmpdir.mkdir("empty_modpacks")
    base_api_url = "https://example.com/api/"
    is_install_on_client = True
    is_install_on_server = False

    # Generate file information for an empty directory
    file_info = generate_file_info(
        root_directory,
        base_api_url,
        is_install_on_client,
        is_install_on_server,
    )

    # The result should be an empty list
    assert not file_info


def test_generate_file_return_invalid_data_for_nested_files(tmpdir):
    """Test generate_file_info() with subdirectories."""
    # Create a directory structure for testing
    root_directory = tmpdir.mkdir("modpacks")
    root_directory.join("file1.txt").write("File 1 content")
    subdirectory = root_directory.mkdir("subdirectory")
    subdirectory.join("file2.txt").write("File 2 content")

    base_api_url = "https://example.com/api/"
    is_install_on_client = True
    is_install_on_server = False

    # Generate file information
    file_info = generate_file_info(
        root_directory,
        base_api_url,
        is_install_on_client,
        is_install_on_server,
    )

    # Check the generated file information
    assert len(file_info) == 2

    # Check the file information for file1.txt
    assert file_info[0]["file_name"] == "file1.txt"
    assert file_info[0]["dist_file_path"] == "file1.txt"
    assert file_info[0]["api_url"] == "https://example.com/api/file1.txt"
    assert file_info[0]["install_on_client"] is True
    assert file_info[0]["install_on_server"] is False
    assert "hash" in file_info[0]
    assert "dist_file_path" in file_info[0]

    # Check the file information for file2.txt in the subdirectory
    assert file_info[1]["file_name"] == "file2.txt"
    assert file_info[1]["dist_file_path"] == "subdirectory\\file2.txt"
    assert (
        file_info[1]["api_url"]
        == "https://example.com/api/subdirectory/file2.txt"
    )
    assert file_info[1]["install_on_client"] is True
    assert file_info[1]["install_on_server"] is False
    assert "hash" in file_info[1]
    assert "dist_file_path" in file_info[1]

    # Add more test cases as needed


def test_generate_json_missing_fields(tmpdir):
    """Test the generate_json() function."""
    # Create a temporary directory for testing
    modpacks_directory = tmpdir.mkdir("modpacks")
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

    # Execute the generate_json function with the specified JSON file path
    map_json = generate_json(modpacks_directory, base_api_url)
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

    # You can add more assertions to check the contents of the JSON file


def test_generate_json_returns_non_empty_dato_for_empty_dir(tmpdir):
    """Test generate_json() with an empty directory."""
    # Create an empty "modpacks" directory for testing
    modpacks_directory = tmpdir.mkdir("modpacks")
    base_api_url = "https://example.com/api/"

    # Execute the generate_json function with an empty directory
    map_json = generate_json(str(modpacks_directory), base_api_url)

    assert not map_json


def test_generate_json_return_nonempry_dict_for_nonexistent_directory(tmpdir):
    """Test generate_json() with a non-existent directory."""
    # Specify a non-existent directory for testing
    non_existent_directory = os.path.join(str(tmpdir), "non_existent_modpacks")
    base_api_url = "https://example.com/api/"

    # Execute the generate_json function with a non-existent directory
    map_json = generate_json(non_existent_directory, base_api_url)

    # Verify that the JSON file is generated (it may be empty)
    assert not map_json


def test_generate_json_return_invalid_fields(tmpdir):
    """Test the file information structure in generate_json()."""
    # Create a temporary directory for testing
    modpacks_directory = tmpdir.mkdir("modpacks")
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

    # Execute the generate_json function with the specified JSON file path
    map_json = generate_json(str(modpacks_directory), base_api_url)

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
