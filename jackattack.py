import os
import sys
import json
import threading
import subprocess
import platform
import requests
import zipfile
import io
from colorama import init, Fore, Style


init(autoreset=True)

class JackAttack:
    def __init__(self):
        self.data_dir = self.get_data_directory()
        self.packages_dir = os.path.join(self.data_dir, 'packages')
        os.makedirs(self.packages_dir, exist_ok=True)
        self.packages = self.load_installed_packages()
        self.running_threads = {}

    def get_data_directory(self):
        if platform.system() == "Windows":
            return os.path.join(os.environ['APPDATA'], 'JackAttack')
        elif platform.system() == "Darwin": 
            return os.path.join(os.environ['HOME'], 'Library', 'Application Support', 'JackAttack')
        else:
            print(Fore.RED + "Unsupported OS")
            exit()

    def load_installed_packages(self):
        packages = {}
        for package_name in os.listdir(self.packages_dir):
            package_path = os.path.join(self.packages_dir, package_name)
            if os.path.isdir(package_path):
                for branch_name in os.listdir(package_path):
                    branch_path = os.path.join(package_path, branch_name)
                    if os.path.isdir(branch_path):
                        pack_json_path = os.path.join(branch_path, 'pack.json')
                        if os.path.isfile(pack_json_path):
                            with open(pack_json_path) as f:
                                package_info = json.load(f)
                            packages[package_info['name']] = {
                                'enabled': False,
                                'folder_name': package_name,
                                'branch_name': branch_name,
                                'info': package_info
                            }
        return packages

    def enable_package(self, package_name):
        if package_name in self.packages:
            self.packages[package_name]['enabled'] = True
            self.run_package(package_name)
        else:
            print(Fore.RED + f"Package '{package_name}' not found.")

    def run_package(self, package_name):
        package_info = self.packages[package_name]
        package_dir = os.path.join(self.packages_dir, package_info['folder_name'])
        branch_dir = os.path.join(package_dir, package_info['branch_name'])
        src_dir = os.path.join(branch_dir, 'src')

        if os.path.exists(src_dir):
            thread = threading.Thread(target=self.execute_package, args=(src_dir, package_name))
            thread.start()
            self.running_threads[package_name] = thread
        else:
            print(Fore.RED + f"No 'src' directory found in package '{package_name}'.")

    def execute_package(self, src_dir, package_name):
        for file in os.listdir(src_dir):
            if file.endswith('.py') and not file.startswith('.'):
                script_path = os.path.join(src_dir, file)
                print(Fore.CYAN + f"Running '{script_path}'...")

                
                if platform.system() == "Windows":
                    python_path = 'pythonw.exe' 
                else:
                    python_path = 'python3'

                command = [python_path, script_path]
                print(f"Command used: {' '.join(command)}") 

              
                try:
                    subprocess.Popen(command)
                except FileNotFoundError as e:
                    print(Fore.RED + f"Failed to run '{script_path}': {e}")

        os._exit(0)

    def download_package(self, repo_url):
       
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        zip_url = repo_url.replace('.git', '/archive/refs/heads/main.zip')

        print(Fore.YELLOW + f"Downloading package from {repo_url}...")

        try:
            response = requests.get(zip_url)
            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                    
                    extract_path = os.path.join(self.packages_dir, repo_name)
                    zip_ref.extractall(extract_path)
                    print(Fore.GREEN + f"Package '{repo_name}' downloaded and extracted.")
            else:
                print(Fore.RED + f"Failed to download package from {repo_url}.")
        except requests.exceptions.RequestException as e:
            print(Fore.RED + f"An error occurred: {e}")

    def list_packages(self):
        if not self.packages:
            print(Fore.YELLOW + "No packages installed.")
            return

        for package_name, package_data in self.packages.items():
            info = package_data['info']
            name = info.get('name', 'Unknown')
            description = info.get('description', 'No description available')
            version = info.get('version', 'Unknown')
            author = info.get('author', 'Unknown')
            branch = package_data['branch_name']

            print(Fore.GREEN + f"Package Name: {name}")
            print(Fore.CYAN + f"Description: {description}")
            print(Fore.MAGENTA + f"Version: {version}")
            print(Fore.BLUE + f"Author: {author}")
            print(Fore.YELLOW + f"Branch: {branch}")
            print(Fore.WHITE + '-' * 40)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='JackAttack Package Manager')
    parser.add_argument('command', choices=['enable', 'list', 'download'], help='The command to execute')
    parser.add_argument('--name', help='The package name for enable')
    parser.add_argument('--url', help='The GitHub repo URL for download')

    args = parser.parse_args()
    manager = JackAttack()

    if args.command == 'enable' and args.name:
        manager.enable_package(args.name)
    elif args.command == 'list':
        manager.list_packages()
    elif args.command == 'download' and args.url:
        manager.download_package(args.url)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
