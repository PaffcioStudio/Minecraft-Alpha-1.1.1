import os
import json
import requests
import zipfile
import hashlib
import shutil
import subprocess
import platform
import string

# === Path to JSON file in script directory ===
json_path = os.path.join(os.path.dirname(__file__), "a1.1.1.json")

# === Main game directory ===
minecraft_dir = os.path.join(os.path.dirname(__file__), "minecraft")
main_dir = os.path.dirname(__file__)  # Folder containing run.py

# === Target directories ===
libraries_folder = os.path.join(minecraft_dir, "libraries")
natives_folder = os.path.join(minecraft_dir, "natives")
temp_natives_folder = os.path.join(natives_folder, "temp")
assets_folder = os.path.join(minecraft_dir, "assets")

# === Create directories if they don't exist ===
os.makedirs(minecraft_dir, exist_ok=True)
os.makedirs(libraries_folder, exist_ok=True)
os.makedirs(natives_folder, exist_ok=True)
os.makedirs(temp_natives_folder, exist_ok=True)
os.makedirs(assets_folder, exist_ok=True)

# === Function to check SHA1 hash ===
def check_sha1(file_path, expected_sha1):
    if not os.path.exists(file_path):
        return False
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha1.update(chunk)
    return sha1.hexdigest() == expected_sha1

# === Function to find Java 8 ===
def find_java_8():
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_bin = os.path.join(java_home, "bin", "java.exe" if platform.system() == "Windows" else "java")
        if os.path.exists(java_bin):
            try:
                output = subprocess.check_output([java_bin, "-version"], stderr=subprocess.STDOUT, text=True)
                if "1.8" in output or "8u" in output:
                    print(f"✅ Found Java 8 at: {java_bin}")
                    return java_bin
            except subprocess.CalledProcessError:
                pass

    possible_paths = [
        "Program Files\\Java\\jdk1.8.0_",
        "Program Files (x86)\\Java\\jdk1.8.0_",
        "Program Files\\Java\\jre1.8.0_",
        "Program Files (x86)\\Java\\jre1.8.0_",
        "Program Files\\AdoptOpenJDK\\jdk-8",
        "Program Files (x86)\\AdoptOpenJDK\\jdk-8"
    ]

    for drive_letter in string.ascii_uppercase:
        drive = f"{drive_letter}:\\"
        for path in possible_paths:
            base_path = os.path.join(drive, path)
            if platform.system() == "Windows":
                for i in range(500, -1, -1):
                    test_path = f"{base_path}{i}\\bin\\java.exe"
                    if os.path.exists(test_path):
                        try:
                            output = subprocess.check_output([test_path, "-version"], stderr=subprocess.STDOUT, text=True)
                            if "1.8" in output or "8u" in output:
                                print(f"✅ Found Java 8 at: {test_path}")
                                return test_path
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
            else:
                test_path = f"{base_path}/bin/java"
                if os.path.exists(test_path):
                    try:
                        output = subprocess.check_output([test_path, "-version"], stderr=subprocess.STDOUT, text=True)
                        if "1.8" in output or "8u" in output:
                            print(f"✅ Found Java 8 at: {test_path}")
                            return test_path
                    except subprocess.CalledProcessError:
                        continue

    print("❌ Java 8 not found! Download JDK or JRE 8 from https://adoptopenjdk.net or https://www.oracle.com/java/")
    return None

# === Download assets ===
def download_assets():
    # New asset source for Alpha a1.1.1
    assets_zip_url = "https://archive.org/download/alpha-1.1.1/resources.zip"
    assets_zip_path = os.path.join(assets_folder, "resources.zip")

    print("📥 Downloading asset resources...\n")
    try:
        if not os.path.exists(assets_zip_path):
            response = requests.get(assets_zip_url, stream=True)
            response.raise_for_status()
            with open(assets_zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Downloaded: {assets_zip_url}")
        else:
            print(f"✅ Resource file already exists: {assets_zip_path}")

        # Extract resources
        print(f"📦 Extracting resources to {assets_folder}")
        with zipfile.ZipFile(assets_zip_path, "r") as zip_ref:
            zip_ref.extractall(os.path.join(assets_folder, "virtual", "legacy"))
        print(f"✅ Extracted resources")
        os.remove(assets_zip_path)
        print(f"🗑️ Deleted temporary file: {assets_zip_path}")
    except Exception as e:
        print(f"❌ Error downloading or extracting assets: {e}")
        print("⚠️ Manually download resources from https://minecraft.wiki/w/Resources or https://archive.org/download/minecraft-resources")
        print("⚠️ Extract to minecraft/assets/virtual/legacy/ (e.g., sound/, music/, textures/)")

# === Load JSON file ===
try:
    with open(json_path, "r") as f:
        version_data = json.load(f)
except Exception as e:
    print(f"❌ Error loading JSON: {e}")
    exit(1)

# === Download libraries ===
print("📥 Downloading libraries...\n")

for lib in version_data["libraries"]:
    if "downloads" in lib and "artifact" in lib["downloads"]:
        artifact = lib["downloads"]["artifact"]
        url = artifact["url"]
        path = artifact.get("path", url.split("/")[-1])
        local_path = os.path.join(libraries_folder, path)
        sha1 = artifact.get("sha1")

        if sha1 and check_sha1(local_path, sha1):
            print(f"✅ Library already exists and is valid: {path}")
            continue

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        print(f"Downloading: {path}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if sha1 and not check_sha1(local_path, sha1):
                print(f"❌ Error: SHA1 mismatch for {path}!")
                os.remove(local_path)
            else:
                print(f"✅ Downloaded: {path}")
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")

# === Download and extract native libraries ===
print("\n📥 Downloading native libraries...\n")

for lib in version_data["libraries"]:
    if "natives" in lib and "windows" in lib["natives"]:
        classifiers = lib["downloads"].get("classifiers", {})
        native_data = classifiers.get("natives-windows")
        if not native_data:
            print(f"⚠️ No native library for Windows in {lib['name']}")
            continue

        url = native_data["url"]
        path = native_data.get("path", url.split("/")[-1])
        local_path = os.path.join(temp_natives_folder, path.split("/")[-1])
        sha1 = native_data.get("sha1")

        if sha1 and check_sha1(local_path, sha1):
            print(f"✅ Native library already exists and is valid: {path}")
        else:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            print(f"Downloading native library: {path}")

            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                if sha1 and not check_sha1(local_path, sha1):
                    print(f"❌ Error: SHA1 mismatch for {path}!")
                    os.remove(local_path)
                    continue
                else:
                    print(f"✅ Downloaded: {path}")
            except Exception as e:
                print(f"❌ Error downloading {url}: {e}")
                continue

        try:
            if os.path.exists(local_path) and (local_path.endswith(".jar") or local_path.endswith(".zip")):
                print(f"📦 Extracting: {path} to {natives_folder}")
                with zipfile.ZipFile(local_path, "r") as zip_ref:
                    zip_ref.extractall(natives_folder)
                print(f"✅ Extracted: {path}")
                os.remove(local_path)
                print(f"🗑️ Deleted temporary file: {path}")
        except Exception as e:
            print(f"❌ Error extracting {path}: {e}")

# === Clean temp folder and META-INF ===
if os.path.exists(temp_natives_folder):
    shutil.rmtree(temp_natives_folder)
    print(f"🗑️ Deleted temporary folder: {temp_natives_folder}")

meta_inf_folder = os.path.join(natives_folder, "META-INF")
if os.path.exists(meta_inf_folder):
    shutil.rmtree(meta_inf_folder)
    print(f"🗑️ Deleted folder: {meta_inf_folder}")

# === Download assets ===
download_assets()

# === Move JAR file to main directory if it's in minecraft folder ===
jar_in_minecraft = os.path.join(minecraft_dir, "a1.1.1.jar")
jar_in_main = os.path.join(main_dir, "a1.1.1.jar")

if os.path.exists(jar_in_minecraft):
    shutil.move(jar_in_minecraft, jar_in_main)
    print(f"📦 Moved JAR file to main directory: {jar_in_main}")

# === Generate start.bat ===
print("\n📝 Generating start.bat...\n")

java_bin = find_java_8()
if not java_bin:
    print("⚠️ Generating start.bat without Java path - set JAVA_HOME or install Java 8.")
    java_cmd = "java"
else:
    java_cmd = f'"{java_bin}"'

bat_content = f"""@echo off
setlocal enabledelayedexpansion

:: === Game filename ===
set MC_JAR=a1.1.1.jar

:: === Main launcher class ===
set MAIN_CLASS={version_data["mainClass"]}

:: === Launcher arguments ===
set MC_ARGS={version_data["minecraftArguments"].replace("${auth_player_name}", "Paffcio").replace("${auth_session}", "token").replace("${game_directory}", "minecraft").replace("${game_assets}", "minecraft/assets")}

:: === Library directory path ===
set LIB_DIR=minecraft\\libraries

:: === Native library directory path ===
set NATIVE_LIB_DIR=minecraft\\natives

:: === Create assets folder if it doesn't exist ===
if not exist minecraft\\assets mkdir minecraft\\assets

:: === Building classpath ===
set CLASSPATH=%LIB_DIR%\\org\\lwjgl\\lwjgl\\lwjgl\\2.9.3-grayscreenfix\\lwjgl-2.9.3-grayscreenfix.jar

for /R "%LIB_DIR%" %%f in (*.jar) do (
    if not "%%f"=="%LIB_DIR%\\org\\lwjgl\\lwjgl\\lwjgl\\2.9.3-grayscreenfix\\lwjgl-2.9.3-grayscreenfix.jar" (
        set CLASSPATH=!CLASSPATH!;%%f
    )
)

:: Add minecraft.jar at the end
set CLASSPATH=!CLASSPATH!;%MC_JAR%

:: === Launch game ===
echo 🚀 Launching Minecraft Alpha a1.1.1... > log.log
{java_cmd} -Djava.library.path="%NATIVE_LIB_DIR%" -Dorg.lwjgl.opengl.Display.allowSoftwareOpenGL=true -Dorg.lwjgl.openal.libname="%NATIVE_LIB_DIR%\\OpenAL32.dll" -cp "!CLASSPATH!" %MAIN_CLASS% %MC_ARGS% >> log.log 2>&1

endlocal
"""

with open(os.path.join(main_dir, "start.bat"), "w", encoding="utf-8") as f:
    f.write(bat_content)

print("✅ Generated start.bat! 🔥")

print("\n✅ All libraries, native libraries, assets downloaded, and start.bat ready! 🚀")
