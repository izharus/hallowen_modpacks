# Minecraft Mod Pack: Server and Client Customizations

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Contents](#contents)
- [JSON File Format](#json-file-format)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Overview
This Minecraft mod pack is designed to enhance your gaming experience by offering a range of customizations for both server and client environments. It provides flexibility for various data types, allowing you to tailor your Minecraft world to your preferences.

## Multiple Server Support

The `map.json` file supports multiple servers. In the modpack directory, you can find separate server folders, such as "terrafirmacraft" and "terrafirmacraft_test" While there may be only one modpack built at the moment, this logic is designed to support multiple modpacks in the future.

If you plan to create additional modpacks, you can organize them in their respective server folders and configure the `map.json` files accordingly. This flexibility allows you to manage and distribute various Minecraft modpacks with ease.

## Getting Started
Follow these steps to get started with the mod pack.

### Prerequisites
- Python 3.11
- Windows 10 (tested platform)

### Installation
1. Clone this repository to your local machine.
2. Set the base URL of your mod repository in the `json_maker_hook.py` file. Example: `"https://raw.githubusercontent.com/izharus/tfc_halloween_modpack/"`.
3. Install the required dependencies by running `pip install -r requirements/dev.txt`.
4. Set up pre-commit hooks to automate the creation and updating of `map.json`. These hooks include linting tools and the `json_maker_hook`, which automatically generates or updates `map.json` when you add new files.
5. Add new files to the repository and commit your changes. The pre-commit hook will take care of updating `map.json`.

## Contents
The mod pack is organized into the following categories:

- **main_data**
  - Compatibility: Server and Client
  - Description: Essential data files for both server and client to ensure compatibility and optimal performance.

- **server_data**
  - Compatibility: Server
  - Description: Server-specific data that enhances gameplay and features on the server side. Install these on your server for an improved gaming experience.

- **client_data**
  - Compatibility: Client
  - Description: Data files intended for clients, providing additional customizations to enhance your personal gameplay. You have the option to install both required and additional data as per your preferences.

- **client_additional_data**
  - Compatibility: Client
  - Description: Additional files that can be added to the client data if needed. The launcher may add some fields to the client data before installation.

## JSON File Format
Each file in the directory should follow a specific JSON format (file_data_dict):

```json
{
  "file_name": "file_name",
  "api_url": "mods/file_name", # used for downloading
  "hash": "hash_value", # hash of the file
  "install_on_client": false, # true if it needs to be installed on the client
  "install_on_server": true, # true if it needs to be installed on the server
  "dist_file_path": "where_to_download_file"
}
```
## Types of Keys in `map.json`

There are four types of keys in the `map.json` file:

- **config**: A dict with config data.
- **main_data**: A list of files that should have fields "install_on_client" and "install_on_server" set to True.

- **client_data**: A list of files where "install_on_client" is True and "install_on_server" is False.

- **server_data**: A list of files that are the same as `client_data`, but intended only for server installation.

- **client_additional_data**: A list of numerous additional files for clients, similar to `client_data`. The launcher may add some fields to `client_data` before installing.

**config** structure:
- **config_name**: The visible name for the current modpack configuration. It should be displayed in the launcher when selecting this configuration.
- **minecraft_version**: The version of Minecraft, for example: "1.18.2".
- **forge_version**: The Forge version, for example: "1.18.2-40.2.9".
- **minecraft_profile**: The name of the Minecraft profile, for example: "1.18.2-forge-40.2.9".
- **minecraft_server_ip**: The IP address of the Minecraft server.
- **minecraft_server_port**: The port of the Minecraft server.

## Usage

This mod pack is ready to enhance your Minecraft experience. Make sure to install the required data on the server and client sides, and customize your game as you see fit.

## Contributing

Feel free to contribute to this mod pack by adding new files, improving documentation, or suggesting enhancements. Create a pull request to share your contributions.

## License

This mod pack is released under the License Name license. See the LICENSE.md file for details.
