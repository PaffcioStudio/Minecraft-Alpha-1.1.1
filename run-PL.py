import os
import json
import requests
import zipfile
import hashlib
import shutil
import subprocess
import platform
import string

# === Ścieżka do pliku JSON w folderze skryptu ===
json_path = os.path.join(os.path.dirname(__file__), "a1.1.1.json")

# === Katalog główny gry ===
minecraft_dir = os.path.join(os.path.dirname(__file__), "minecraft")
main_dir = os.path.dirname(__file__)  # Folder z run.py

# === Foldery docelowe ===
libraries_folder = os.path.join(minecraft_dir, "libraries")
natives_folder = os.path.join(minecraft_dir, "natives")
temp_natives_folder = os.path.join(natives_folder, "temp")
assets_folder = os.path.join(minecraft_dir, "assets")

# === Tworzenie folderów, jeśli nie istnieją ===
os.makedirs(minecraft_dir, exist_ok=True)
os.makedirs(libraries_folder, exist_ok=True)
os.makedirs(natives_folder, exist_ok=True)
os.makedirs(temp_natives_folder, exist_ok=True)
os.makedirs(assets_folder, exist_ok=True)

# === Funkcja do sprawdzania sumy SHA1 ===
def check_sha1(file_path, expected_sha1):
    if not os.path.exists(file_path):
        return False
    sha1 = hashlib.sha1()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha1.update(chunk)
    return sha1.hexdigest() == expected_sha1

# === Funkcja do wyszukiwania Java 8 ===
def find_java_8():
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_bin = os.path.join(java_home, "bin", "java.exe" if platform.system() == "Windows" else "java")
        if os.path.exists(java_bin):
            try:
                output = subprocess.check_output([java_bin, "-version"], stderr=subprocess.STDOUT, text=True)
                if "1.8" in output or "8u" in output:
                    print(f"✅ Znaleziono Java 8 w: {java_bin}")
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
                                print(f"✅ Znaleziono Java 8 w: {test_path}")
                                return test_path
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            continue
            else:
                test_path = f"{base_path}/bin/java"
                if os.path.exists(test_path):
                    try:
                        output = subprocess.check_output([test_path, "-version"], stderr=subprocess.STDOUT, text=True)
                        if "1.8" in output or "8u" in output:
                            print(f"✅ Znaleziono Java 8 w: {test_path}")
                            return test_path
                    except subprocess.CalledProcessError:
                        continue

    print("❌ Nie znaleziono Java 8! Pobierz JDK lub JRE 8 z https://adoptopenjdk.net lub https://www.oracle.com/java/")
    return None

# === Pobieranie assetów ===
def download_assets():
    # Nowe źródło assetów dla Alpha a1.1.1
    assets_zip_url = "https://archive.org/download/alpha-1.1.1/resources.zip"
    assets_zip_path = os.path.join(assets_folder, "resources.zip")

    print("📥 Pobieranie zasobów assetów...\n")
    try:
        if not os.path.exists(assets_zip_path):
            response = requests.get(assets_zip_url, stream=True)
            response.raise_for_status()
            with open(assets_zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Pobrano: {assets_zip_url}")
        else:
            print(f"✅ Plik zasobów już istnieje: {assets_zip_path}")

        # Rozpakowanie zasobów
        print(f"📦 Rozpakowywanie zasobów do {assets_folder}")
        with zipfile.ZipFile(assets_zip_path, "r") as zip_ref:
            zip_ref.extractall(os.path.join(assets_folder, "virtual", "legacy"))
        print(f"✅ Rozpakowano zasoby")
        os.remove(assets_zip_path)
        print(f"🗑️ Usunięto tymczasowy plik: {assets_zip_path}")
    except Exception as e:
        print(f"❌ Błąd przy pobieraniu lub rozpakowywaniu assetów: {e}")
        print("⚠️ Ręcznie pobierz zasoby z https://minecraft.wiki/w/Resources lub https://archive.org/download/minecraft-resources")
        print("⚠️ Rozpakuj do minecraft/assets/virtual/legacy/ (np. sound/, music/, textures/)")

# === Wczytanie pliku JSON ===
try:
    with open(json_path, "r") as f:
        version_data = json.load(f)
except Exception as e:
    print(f"❌ Błąd wczytywania JSON: {e}")
    exit(1)

# === Pobieranie bibliotek ===
print("📥 Pobieranie bibliotek...\n")

for lib in version_data["libraries"]:
    if "downloads" in lib and "artifact" in lib["downloads"]:
        artifact = lib["downloads"]["artifact"]
        url = artifact["url"]
        path = artifact.get("path", url.split("/")[-1])
        local_path = os.path.join(libraries_folder, path)
        sha1 = artifact.get("sha1")

        if sha1 and check_sha1(local_path, sha1):
            print(f"✅ Biblioteka już istnieje i jest poprawna: {path}")
            continue

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        print(f"Pobieram: {path}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if sha1 and not check_sha1(local_path, sha1):
                print(f"❌ Błąd: Suma SHA1 dla {path} się nie zgadza!")
                os.remove(local_path)
            else:
                print(f"✅ Pobrano: {path}")
        except Exception as e:
            print(f"❌ Błąd przy pobieraniu {url}: {e}")

# === Pobieranie i rozpakowywanie natywnych bibliotek ===
print("\n📥 Pobieranie natywnych bibliotek...\n")

for lib in version_data["libraries"]:
    if "natives" in lib and "windows" in lib["natives"]:
        classifiers = lib["downloads"].get("classifiers", {})
        native_data = classifiers.get("natives-windows")
        if not native_data:
            print(f"⚠️ Brak natywnej biblioteki dla Windows w {lib['name']}")
            continue

        url = native_data["url"]
        path = native_data.get("path", url.split("/")[-1])
        local_path = os.path.join(temp_natives_folder, path.split("/")[-1])
        sha1 = native_data.get("sha1")

        if sha1 and check_sha1(local_path, sha1):
            print(f"✅ Natywna biblioteka już istnieje i jest poprawna: {path}")
        else:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            print(f"Pobieram natywną bibliotekę: {path}")

            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                if sha1 and not check_sha1(local_path, sha1):
                    print(f"❌ Błąd: Suma SHA1 dla {path} się nie zgadza!")
                    os.remove(local_path)
                    continue
                else:
                    print(f"✅ Pobrano: {path}")
            except Exception as e:
                print(f"❌ Błąd przy pobieraniu {url}: {e}")
                continue

        try:
            if os.path.exists(local_path) and (local_path.endswith(".jar") or local_path.endswith(".zip")):
                print(f"📦 Rozpakowywanie: {path} do {natives_folder}")
                with zipfile.ZipFile(local_path, "r") as zip_ref:
                    zip_ref.extractall(natives_folder)
                print(f"✅ Rozpakowano: {path}")
                os.remove(local_path)
                print(f"🗑️ Usunięto tymczasowy plik: {path}")
        except Exception as e:
            print(f"❌ Błąd przy rozpakowywaniu {path}: {e}")

# === Czyszczenie folderu temp i META-INF ===
if os.path.exists(temp_natives_folder):
    shutil.rmtree(temp_natives_folder)
    print(f"🗑️ Usunięto folder tymczasowy: {temp_natives_folder}")

meta_inf_folder = os.path.join(natives_folder, "META-INF")
if os.path.exists(meta_inf_folder):
    shutil.rmtree(meta_inf_folder)
    print(f"🗑️ Usunięto folder: {meta_inf_folder}")

# === Pobieranie assetów ===
download_assets()

# === Przenoszenie pliku JAR do głównego folderu jeśli jest w minecraft ===
jar_in_minecraft = os.path.join(minecraft_dir, "a1.1.1.jar")
jar_in_main = os.path.join(main_dir, "a1.1.1.jar")

if os.path.exists(jar_in_minecraft):
    shutil.move(jar_in_minecraft, jar_in_main)
    print(f"📦 Przeniesiono plik JAR do głównego folderu: {jar_in_main}")

# === Generowanie start.bat ===
print("\n📝 Generowanie start.bat...\n")

java_bin = find_java_8()
if not java_bin:
    print("⚠️ Generowanie start.bat bez wskazania Javy – ustaw JAVA_HOME lub zainstaluj Java 8.")
    java_cmd = "java"
else:
    java_cmd = f'"{java_bin}"'

bat_content = f"""@echo off
setlocal enabledelayedexpansion

:: === Nazwa pliku gry ===
set MC_JAR=a1.1.1.jar

:: === Główna klasa launchera ===
set MAIN_CLASS={version_data["mainClass"]}

:: === Argumenty launchera ===
set MC_ARGS={version_data["minecraftArguments"].replace("${auth_player_name}", "Paffcio").replace("${auth_session}", "token").replace("${game_directory}", "minecraft").replace("${game_assets}", "minecraft/assets")}

:: === Ścieżka do katalogu z bibliotekami ===
set LIB_DIR=minecraft\\libraries

:: === Ścieżka do katalogu z natywnymi bibliotekami ===
set NATIVE_LIB_DIR=minecraft\\natives

:: === Tworzenie folderu assets, jeśli nie istnieje ===
if not exist minecraft\\assets mkdir minecraft\\assets

:: === Składanie classpath ===
set CLASSPATH=%LIB_DIR%\\org\\lwjgl\\lwjgl\\lwjgl\\2.9.3-grayscreenfix\\lwjgl-2.9.3-grayscreenfix.jar

for /R "%LIB_DIR%" %%f in (*.jar) do (
    if not "%%f"=="%LIB_DIR%\\org\\lwjgl\\lwjgl\\lwjgl\\2.9.3-grayscreenfix\\lwjgl-2.9.3-grayscreenfix.jar" (
        set CLASSPATH=!CLASSPATH!;%%f
    )
)

:: Dodajemy minecraft.jar na koniec
set CLASSPATH=!CLASSPATH!;%MC_JAR%

:: === Uruchamianie gry ===
echo 🚀 Uruchamianie Minecraft Alpha a1.1.1... > log.log
{java_cmd} -Djava.library.path="%NATIVE_LIB_DIR%" -Dorg.lwjgl.opengl.Display.allowSoftwareOpenGL=true -Dorg.lwjgl.openal.libname="%NATIVE_LIB_DIR%\\OpenAL32.dll" -cp "!CLASSPATH!" %MAIN_CLASS% %MC_ARGS% >> log.log 2>&1

endlocal
"""

with open(os.path.join(main_dir, "start.bat"), "w", encoding="utf-8") as f:
    f.write(bat_content)

print("✅ Wygenerowano start.bat! 🔥")

print("\n✅ Wszystkie biblioteki, natywne biblioteki, assety pobrane, a start.bat gotowy! 🚀")
