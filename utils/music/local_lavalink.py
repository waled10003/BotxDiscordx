# -*- coding: utf-8 -*-
import os
import platform
import re
import shutil
import subprocess
import time
import zipfile

import requests


def download_file(url, filename):

    if os.path.isfile(filename):
        return

    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length', 0))
    bytes_downloaded = 0
    previows_progress = 0
    start_time = time.time()

    if total_size >= 1024 * 1024:
        total_txt = f"{total_size / (1024 * 1024):.2f} MB"
    else:
        total_txt = f"{total_size / 1024:.2f} KB"

    with open(filename, 'wb') as f:

        for data in r.iter_content(chunk_size=2500*1024):
            f.write(data)
            bytes_downloaded += len(data)
            current_progress = int((bytes_downloaded / total_size) * 100)

            if current_progress != previows_progress:
                previows_progress = current_progress
                time_elapsed = time.time() - start_time
                download_speed = bytes_downloaded / time_elapsed / 1024
                if download_speed >= 1:
                    download_speed = (download_speed or 1) / 1024
                    speed_txt = "MB/s"
                else:
                    speed_txt = "KB/s"
                print(f"Download do arquivo {filename} {current_progress}% concluído ({download_speed:.2f} {speed_txt} / {total_txt})")

    r.close()

    return True

def validate_java(cmd: str, debug: bool = False):
    try:
        java_info = subprocess.check_output(f'{cmd} -version', shell=True, stderr=subprocess.STDOUT)
        java_version = re.search(r'\d+', java_info.decode().split("\r")[0]).group().replace('"', '')
        if int(java_version.split('.')[0]) >= 17:
            return cmd
    except Exception as e:
        if debug:
            print(f"\nFalha ao obter versão do java...\n"
                  f"Path: {cmd} | Erro: {repr(e)}\n")

def run_lavalink(
        lavalink_file_url: str = None,
        lavalink_initial_ram: int = 30,
        lavalink_ram_limit: int = 100,
        lavalink_additional_sleep: int = 0,
        lavalink_cpu_cores: int = 1,
        use_jabba: bool = True
):

    if not (java_cmd := validate_java("java")):

        dirs = []

        try:
            dirs.append(os.path.join(os.environ["JAVA_HOME"] + "bin/java"))
        except KeyError:
            pass

        if os.name == "nt":
            dirs.append(os.path.realpath("./.java/jdk-17.0.9/bin/java"))
            try:
                shutil.rmtree("./.jabba")
            except:
                pass

        else:
            if use_jabba:
                dirs.extend(
                    [
                        os.path.realpath("./.jabba/jdk/zulu@1.17.0-0/bin/java"),
                        os.path.expanduser("~/.jabba/jdk/zulu@1.17.0-0/bin/java")
                    ]
                )
                try:
                    shutil.rmtree("./.java")
                except:
                    pass

            else:
                dirs.append(os.path.realpath("./.java/jdk-17.0.9/bin/java"))
                try:
                    shutil.rmtree("./.jabba")
                except:
                    pass

        for cmd in dirs:
            if validate_java(cmd):
                java_cmd = cmd
                break

        if not java_cmd:

            if os.name == "nt":

                try:
                    shutil.rmtree("./.java")
                except:
                    pass

                if platform.architecture()[0] != "64bit":
                    jdk_url = "https://download.bell-sw.com/java/17.0.9+11/bellsoft-jdk17.0.9+11-windows-i586.zip"
                else:
                    jdk_url = "https://download.bell-sw.com/java/17.0.9+11/bellsoft-jdk17.0.9+11-windows-amd64.zip"

                jdk_filename = "java.zip"

                download_file(jdk_url, jdk_filename)

                with zipfile.ZipFile(jdk_filename, 'r') as zip_ref:
                    zip_ref.extractall("./.java")

                os.remove(jdk_filename)

                java_cmd = os.path.realpath("./.java/jdk-17.0.9/bin/java")

            elif use_jabba:

                try:
                    shutil.rmtree("~/.jabba/jdk/zulu@1.17.0-0")
                except:
                    pass

                download_file("https://github.com/shyiko/jabba/raw/master/install.sh", "install_jabba.sh")
                subprocess.call("bash install_jabba.sh".split())
                subprocess.call("~/.jabba/bin/jabba install zulu@>=1.17.0-0", shell=True)
                os.remove("install_jabba.sh")

                java_cmd = os.path.expanduser("~/.jabba/jdk/zulu@1.17.0-0/bin/java")

            else:
                if not os.path.isdir("./.java"):

                    if platform.architecture()[0] != "64bit":
                        jdk_url = "https://download.bell-sw.com/java/17.0.9+11/bellsoft-jdk17.0.9+11-linux-i586.tar.gz"
                    else:
                        jdk_url = "https://download.bell-sw.com/java/17.0.9+11/bellsoft-jdk17.0.9+11-linux-amd64.tar.gz"

                    java_cmd = os.path.realpath("./.java/jdk-17.0.9/bin/java")

                    jdk_filename = "java.tar.gz"

                    download_file(jdk_url, jdk_filename)

                    try:
                        shutil.rmtree("./.java")
                    except:
                        pass

                    os.makedirs("./.java")

                    p = subprocess.Popen(["tar", "-zxvf", "java.tar.gz", "-C", "./.java"])
                    p.wait()
                    os.remove(f"./{jdk_filename}")

                else:
                    java_cmd = os.path.realpath("./.java/jdk-17.0.9/bin/java")

    clear_plugins = False

    for filename, url in (
        ("Lavalink.jar", lavalink_file_url),
        ("application.yml", "https://github.com/zRitsu/LL-binaries/releases/download/0.0.1/application.yml")
    ):
        if download_file(url, filename):
            clear_plugins = True

    if lavalink_cpu_cores >= 1:
        java_cmd += f" -XX:ActiveProcessorCount={lavalink_cpu_cores}"

    if lavalink_ram_limit > 10:
        java_cmd += f" -Xmx{lavalink_ram_limit}m"

    if 0 < lavalink_initial_ram < lavalink_ram_limit:
        java_cmd += f" -Xms{lavalink_ram_limit}m"

    java_cmd += " -jar Lavalink.jar"

    if clear_plugins:
        try:
            shutil.rmtree("./plugins")
        except:
            pass

    print(f"Iniciando o servidor Lavalink (dependendo da hospedagem o lavalink pode demorar iniciar, "
          f"o que pode ocorrer falhas em algumas tentativas de conexão até ele iniciar totalmente).\n{'-' * 30}")

    lavalink_process = subprocess.Popen(java_cmd.split(), stdout=subprocess.DEVNULL)

    if lavalink_additional_sleep:
        print(f"Aguarde {lavalink_additional_sleep} segundos...\n{'-' * 30}")
        time.sleep(lavalink_additional_sleep)

    return lavalink_process