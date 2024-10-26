# Minecraft Mod Pack: Server and Client Customizations

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Contents](#contents)
- [JSON File Format](#json-file-format)

## Overview
This script generates map.json files, which represent file structures and configuration data for installing Minecraft modpacks.

## Multiple Server Support
The `map.json` file supports multiple servers. In the modpack directory, you can find separate server folders (modpack), such as "terrafirmacraft" and "terrafirmacraft_test" While there may be only one modpack built at the moment, this logic is designed to support multiple modpacks in the future.

If you plan to create additional modpacks, you can organize them in their respective server folders and configure the `map.json` files accordingly. This flexibility allows you to manage and distribute various Minecraft modpacks with ease.

## Getting Started
Follow these steps to get started with the mod pack.

### Prerequisites
- Python 3.11
- Windows 10+ (Windows 8 was not tested)

### Installation
1. Clone this repository to your local machine.
2. Set the base URL of your mod repository in the `json_maker_hook.py` file. Example: `"https://raw.githubusercontent.com/izharus/tfc_halloween_modpack/"`.
3. Set your credentials for Yandex Object Storage:  
ACCESS_KEY, SECRET_KEY, REGION_NAME, BUCKET_NAME
4. Install the required dependencies by running `pip install -r requirements/dev.txt`.
5. Set up pre-commit hooks to automate the creation and updating of `map.json`. These hooks include linting tools and the `json_maker_hook`, which automatically generates or updates `map.json` when you add new files.
6. Add new files to the repository and commit your changes. The pre-commit hook will take care of updating `map.json`.

## Contents
All modpacks store in the "modpacks" directory. Every modpack stores in its own directory (modpack_name).  

- **modpack_name/server_config.json**
  - This files contains a configuration data for installing and executing Vanilla Minecraft.
 
- **modpack_name/main_data/**
  - Essential data files for both server and client.

- **modpack_name/client_additional_data/launcher_data/**
  - A directory for storing some additional data for launcher:
    - server_icon.jpg

- **modpack_name/client_additional_data/custom_name**
  - Additional files that can be added to the client data if needed. It could be multiple "custom_name" dirs.


## JSON File Format
Every file from "modpack_name" dir represents by the json structure (file_info):

```json
{
  "file_name": "file_name",
  "api_url": "https://raw.githubusercontent.com/...", // used for downloading file/
  "yan_obj_storage": "key/to/file/file.ext", // object key to the file in yan obj storage
  "hash": "hash_value", // hash of the file
  "dist_file_path": "where_to_download_file"
}
```


## server_config.json structure:
This file represents a json dictionary (server_config):
```json
{
  "display_name" : "TFC Survival", //The visible name for the current modpack configuration. It should be displayed in the launcher when selecting this configuration.
  "minecraft_version": "1.18.2", // The version of Minecraft.
  "forge_version": "1.18.2-40.2.9", // The Forge version.
  "minecraft_profile": "1.18.2-forge-40.2.9", // The name of the Minecraft profile.
  "minecraft_server_ip": "123.123.123.123", // The IP address of the Minecraft server.
  "minecraft_server_port": "5610", //The port of the Minecraft server.
  "description": "Server description", // A minecraft server description for launcher
  "server_icon": file_info, // A server icon for launcher
}
```


## `map.json` example:
```json
{
  "terrafirmacraft": {
    "server_config": {}, // An instance of server_config.json for current modpack.
    "main_data": [], // A list of file_info objects for current directory".
    "client_additional_data": {
      "shaders": [], // A list of file_info objects for current directory".
      "fancy_interface": [], // A list of file_info objects for current directory".
    }
  },
  "skyblock": {
    "server_config": {}, // An instance of server_config.json for current modpack.
    "main_data": [], // A list of file_info objects for current directory".
    "client_additional_data": {} // Empty for current server.
  }
}
For more information look into pydantic models (src/pydantic_model.py).

```
