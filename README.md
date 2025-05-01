
# Minecraft Alpha A1.1.1 Setup Script

This is a Python script designed to set up and prepare the environment for running **Minecraft Alpha 1.1.1 with fix no gray screen**.

## Features

- Downloads and extracts the necessary assets for Minecraft Alpha 1.1.1.
- Downloads required libraries from URLs specified in a `JSON` configuration file.
- Checks and verifies the integrity of downloaded files using `SHA1` hash checks.
- Automatically locates Java 8 on your system, which is required to run Minecraft.
- Supports custom library and asset paths for flexibility.

## Requirements

- **Python 3.x** (Make sure `python` command is available in your terminal)
- **Java 8** (JDK or JRE) - Minecraft Alpha 1.1.1 requires Java 8. You can download it from [AdoptOpenJDK](https://adoptopenjdk.net) or [Oracle](https://www.oracle.com/java/).

### Python Dependencies
To run this script, you need to install the following Python libraries:

```bash
pip install requests
```

## Installation and Setup

1. Clone the repository or download the script to your local machine.
   
2. **Install Python Dependencies**:

   Run the following command to install the required libraries:
   
   ```bash
   pip install -r requirements.txt
   ```

   If you don't have the `requirements.txt` file, you can manually install `requests` via:
   
   ```bash
   pip install requests
   ```

3. **Download Minecraft Alpha 1.1.1 Resources**:

   - The script will automatically attempt to download and extract the necessary assets to your system.
   - If the automatic download fails, please manually download the required resources from:
     - [Minecraft Wiki](https://minecraft.wiki/w/Resources)
     - [Internet Archive - Minecraft Alpha 1.1.1](https://archive.org/download/alpha-1.1.1/resources.zip)
     - [My GitHub]_(https://github.com/PaffcioStudio/Minecraft-Alpha-1.1.1/tree/main/resources)
   - Extract the files into `minecraft/assets/virtual/legacy/`.

4. **Run the Script**:

   Simply execute the script by running:
   
English version:
   ```bash
   python run-EN.py
   ```

Polish version:
   ```bash
   python run-PL.py
   ```

   The script will:
   - Check for Java 8 installation.
   - Download missing libraries and assets.
   - Set up necessary directories and files for Minecraft Alpha 1.1.1.

5. **Verify Java Installation**:
   
   If you don't have Java 8, the script will notify you and give a link to download it.

## Directory Structure

- `minecraft/`: The root directory where Minecraft files are placed.
- `minecraft/libraries/`: Directory containing all the libraries.
- `minecraft/natives/`: Native files for running Minecraft.
- `minecraft/assets/`: Assets (textures, sounds, etc.) for the game.

## Troubleshooting

- **Java 8 Not Found**: The script will attempt to locate Java 8 on your system. If it can't find it, ensure that you have Java 8 installed and properly set in your `JAVA_HOME` environment variable.
  
- **Asset Download Failures**: If the script fails to download the assets, download them manually from the provided sources and extract them into the correct directory as described above.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
