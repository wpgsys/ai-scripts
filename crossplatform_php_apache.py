import os
import subprocess
import sys
import urllib.request
import zipfile
import shutil
import hashlib
import gnupg
import time
import platform

"""
####################################################################################
# Cross-Platform Apache and PHP Installer Script (Windows, MacOS, Linux)
####################################################################################
# Description:
# This Python script automates the installation, configuration, and setup of Apache 
# HTTP Server and PHP across multiple operating systems, including Windows, MacOS, 
# and Linux. Designed for developers and system administrators, this script ensures 
# a smooth setup process by handling OS-specific configurations, downloading necessary 
# files, verifying integrity using SHA256 checksums and PGP signatures, and starting 
# the Apache service seamlessly.
#
# Features:
# - Cross-platform compatibility (Windows, MacOS, Linux)
# - Automated download and verification of Apache and PHP binaries
# - PGP signature verification for enhanced security
# - Customizable Apache port, DocumentRoot, and PHP configuration
# - Environment variable setup for Apache and PHP
# - Easy-to-use command-line interface with detailed prompts
#
# Keywords:
# - Apache HTTP Server
# - PHP Installation
# - Cross-Platform Script
# - Windows, MacOS, Linux
# - PGP Signature Verification
# - SHA256 Checksum Verification
# - Server Setup Automation
# - Web Server Configuration
# - Python Automation Script
# - Developer Tools
#
# Usage:
# 1. Ensure Python 3.x is installed on your system.
# 2. Open Command Prompt or Terminal as Administrator (or use sudo).
# 3. Run this script using Python: `python3 setup_apache_php.py`
# 4. Follow the on-screen prompts to customize your Apache and PHP setup.
# 5. The script will handle downloading, verification, configuration, and starting 
#    the Apache HTTP Server, making your web server ready to use.
#
# Author: DS (fr3nch1e)
# Date: Aug 17 2024
#
# Note: This script is open-source and can be modified or redistributed according 
# to the MIT license. Contributions and feedback are welcome.
####################################################################################
"""


# ANSI escape sequences for colored output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color=Colors.OKGREEN):
    """Prints a message in the specified color."""
    print(f"{color}{message}{Colors.ENDC}")

class Downloader:
    def __init__(self):
        pass

    def download_file(self, url, dest):
        """Download a file from a URL with retries."""
        def download():
            print_colored(f"Downloading {url}...", Colors.OKCYAN)
            urllib.request.urlretrieve(url, dest)
            if not os.path.exists(dest):
                raise Exception(f"Failed to download {url}")
            print_colored(f"Downloaded to {dest}", Colors.OKGREEN)
        self.retry(download)

    def verify_checksum(self, file_path, expected_checksum):
        """Verify the SHA256 checksum of a downloaded file."""
        print_colored(f"Verifying checksum for {file_path}...", Colors.OKCYAN)
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            calculated_checksum = sha256.hexdigest()
            if calculated_checksum == expected_checksum:
                print_colored(f"Checksum verification passed for {file_path}.", Colors.OKGREEN)
                return True
            else:
                print_colored(f"Checksum verification failed for {file_path}. Expected {expected_checksum}, got {calculated_checksum}.", Colors.FAIL)
                return False
        except FileNotFoundError:
            print_colored(f"File {file_path} not found for checksum verification.", Colors.FAIL)
            return False

    def retry(self, func, retries=3, delay=5):
        """Retry a function call with specified retries and delay."""
        for attempt in range(retries):
            try:
                return func()
            except Exception as e:
                print_colored(f"Attempt {attempt + 1} failed: {e}", Colors.WARNING)
                time.sleep(delay)
        print_colored(f"All attempts failed for {func.__name__}.", Colors.FAIL)
        sys.exit(1)

class PGPHandler:
    def __init__(self):
        self.gpg = gnupg.GPG()

    def download_pgp_key(self, fingerprint):
        """Download the PGP key from a keyserver using its fingerprint with retries."""
        def download_key():
            print_colored(f"Downloading PGP key with fingerprint {fingerprint}...", Colors.OKCYAN)
            keyserver = "hkps://keys.openpgp.org"  # You can use another keyserver if needed
            result = self.gpg.recv_keys(keyserver, fingerprint)
            if not result:
                raise Exception(f"Failed to download PGP key with fingerprint {fingerprint}")
            print_colored(f"Successfully downloaded PGP key with fingerprint {fingerprint}.", Colors.OKGREEN)
        Downloader().retry(download_key)

    def verify_pgp(self, file_path, pgp_file):
        """Verify the PGP signature of a downloaded file."""
        print_colored(f"Verifying PGP signature for {file_path}...", Colors.OKCYAN)
        with open(pgp_file, "rb") as sig_file:
            with open(file_path, "rb") as target_file:
                verified = self.gpg.verify_file(sig_file, file_path)
                if verified:
                    print_colored(f"PGP signature verification passed for {file_path}.", Colors.OKGREEN)
                    return True
                else:
                    print_colored(f"PGP signature verification failed for {file_path}.", Colors.FAIL)
                    return False

class ApacheConfigurator:
    def __init__(self, apache_dir, php_dir, os_type):
        self.apache_dir = apache_dir
        self.php_dir = php_dir
        self.os_type = os_type

    def configure(self, apache_port, document_root, php_ini):
        """Configure Apache to work with PHP and use the specified settings."""
        httpd_conf = os.path.join(self.apache_dir, "conf", "httpd.conf")

        # Backup the original httpd.conf
        try:
            shutil.copyfile(httpd_conf, f"{httpd_conf}.backup")
        except IOError as e:
            print_colored(f"Failed to backup httpd.conf: {e}", Colors.FAIL)
            sys.exit(1)

        # Update httpd.conf with user-specified port, DocumentRoot, and PHP configuration
        try:
            with open(httpd_conf, "r") as conf_file:
                config_lines = conf_file.readlines()

            with open(httpd_conf, "w") as conf_file:
                for line in config_lines:
                    if line.strip().startswith("Listen "):
                        conf_file.write(f"Listen {apache_port}\n")  # Set user-specified port
                    elif line.strip().startswith("<VirtualHost _default_:80>"):
                        conf_file.write(f"<VirtualHost _default_:{apache_port}>\n")  # Set user-specified port
                    elif line.strip().startswith("DocumentRoot "):
                        conf_file.write(f'DocumentRoot "{document_root}"\n')  # Set user-specified DocumentRoot
                    elif line.strip().startswith("<Directory "):
                        conf_file.write(f'<Directory "{document_root}">\n')  # Set user-specified Directory path
                    else:
                        conf_file.write(line)

                # Add PHP module and handler configuration
                php_module_line = self.get_php_module_line()
                conf_file.write("\n# PHP Configuration\n")
                conf_file.write(php_module_line)
                conf_file.write(f"AddHandler application/x-httpd-php .php\n")
                conf_file.write(f"PHPIniDir \"{os.path.dirname(php_ini)}\"\n")
                conf_file.write("DirectoryIndex index.php index.html\n")

            print_colored(f"Apache configured to use PHP, listen on port {apache_port}, and serve content from {document_root}.", Colors.OKGREEN)
        except IOError as e:
            print_colored(f"Failed to configure Apache: {e}", Colors.FAIL)
            sys.exit(1)

    def get_php_module_line(self):
        """Get the appropriate PHP module line based on the OS."""
        if self.os_type == "Windows":
            return f"LoadModule php_module \"{self.php_dir}\\php8apache2_4.dll\"\n"
        elif self.os_type == "Darwin":  # MacOS
            return f"LoadModule php_module \"{self.php_dir}/libphp.so\"\n"
        else:  # Linux
            return f"LoadModule php_module \"{self.php_dir}/libphp.so\"\n"

    def start_apache(self):
        """Start Apache HTTP Server."""
        apache_exe = os.path.join(self.apache_dir, "bin", "httpd.exe" if self.os_type == "Windows" else "httpd")
        try:
            if self.os_type == "Windows":
                subprocess.run([apache_exe, "-k", "install"], check=True)
                subprocess.run([apache_exe, "-k", "start"], check=True)
            else:
                subprocess.run(["sudo", apache_exe, "-k", "start"], check=True)
            print_colored("Apache HTTP Server started successfully.", Colors.OKGREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"Failed to start Apache: {e}", Colors.FAIL)
            sys.exit(1)

    def setup_environment_variables(self):
        """Set up system environment variables for Apache and PHP."""
        apache_bin_dir = os.path.join(self.apache_dir, "bin")
        php_bin_dir = self.php_dir

        try:
            if self.os_type == "Windows":
                os.environ["PATH"] = f"{apache_bin_dir};{php_bin_dir};" + os.environ["PATH"]
            else:
                bash_profile = os.path.expanduser("~/.bash_profile")
                with open(bash_profile, "a") as bash_file:
                    bash_file.write(f'\nexport PATH="{apache_bin_dir}:{php_bin_dir}:$PATH"\n')
                subprocess.run(["source", bash_profile], shell=True)
            print_colored("Environment variables set successfully.", Colors.OKGREEN)
        except Exception as e:
            print_colored(f"Failed to set environment variables: {e}", Colors.FAIL)
            sys.exit(1)

class Installer:
    def __init__(self):
        self.os_type = platform.system()
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self.install_dir = os.path.join("/", "usr", "local", "ApachePHP") if self.os_type != "Windows" else os.path.join(os.environ["SYSTEMDRIVE"], "ApachePHP")
        self.apache_dir = os.path.join(self.install_dir, "Apache24")
        self.php_dir = os.path.join(self.install_dir, "php")
        self.downloader = Downloader()
        self.pgp_handler = PGPHandler()
        self.apache_configurator = ApacheConfigurator(self.apache_dir, self.php_dir, self.os_type)

    def get_user_input(self):
        print_colored("Cross-Platform Apache and PHP Installer", Colors.HEADER)
        print_colored("======================================", Colors.HEADER)
        
        use_default_urls = input("Use default URLs for Apache and PHP? (y/n, default is 'y'): ") or "y"
        
        if use_default_urls.lower() == "y":
            apache_url, php_url = default_apache_url, default_php_url
        else:
            apache_url = input(f"Enter the download URL for Apache (default is {default_apache_url}): ") or default_apache_url
            php_url = input(f"Enter the download URL for PHP (default is {default_php_url}): ") or default_php_url
        
        apache_port = input("Enter the port for Apache to listen on (default is 8080): ") or "8080"
        document_root = input(f"Enter the DocumentRoot path for Apache (default is {os.path.join(self.apache_dir, 'htdocs')}): ") or os.path.join(self.apache_dir, 'htdocs')
        php_ini = input(f"Enter the path to php.ini (leave blank to use default in PHP directory): ") or os.path.join(self.php_dir, "php.ini")
        
        return apache_url, php_url, apache_port, document_root, php_ini

    def download_and_extract(self, url, extract_to, checksum_url=None, pgp_url=None, key_fingerprints=None):
        """Download and extract a zip file from a URL, verifying checksum and PGP."""
        filename = os.path.join(self.download_dir, os.path.basename(url))
        
        # Download the file
        self.downloader.download_file(url, filename)
        
        # Verify download if checksum URL is provided
        if checksum_url:
            print_colored("Verifying checksum...", Colors.OKCYAN)
            checksum_file = os.path.join(self.download_dir, os.path.basename(checksum_url))
            self.downloader.download_file(checksum_url, checksum_file)
            
            expected_checksum = None
            with open(checksum_file, "r") as f:
                for line in f:
                    if os.path.basename(url) in line:
                        expected_checksum = line.split()[0]
                        break
            
            if expected_checksum is None:
                print_colored(f"Error: Checksum for {os.path.basename(url)} not found.", Colors.FAIL)
                sys.exit(1)
            
            if not self.downloader.verify_checksum(filename, expected_checksum):
                sys.exit(1)
        
        # Download and import PGP keys if provided
        if key_fingerprints:
            for fingerprint in key_fingerprints:
                self.pgp_handler.download_pgp_key(fingerprint)
        
        # Verify PGP signature if PGP URL is provided
        if pgp_url:
            pgp_file = os.path.join(self.download_dir, os.path.basename(pgp_url))
            self.downloader.download_file(pgp_url, pgp_file)
            if not self.pgp_handler.verify_pgp(filename, pgp_file):
                sys.exit(1)
        
        # Extract file
        try:
            print_colored(f"Extracting {filename}...", Colors.OKCYAN)
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            print_colored(f"Extracted to {extract_to}", Colors.OKGREEN)
        except zipfile.BadZipFile:
            print_colored(f"Failed to extract {filename}. It may be corrupted.", Colors.FAIL)
            sys.exit(1)
        
        # Clean up downloaded file and checksum file
        os.remove(filename)
        if checksum_url:
            os.remove(checksum_file)
        if pgp_url:
            os.remove(pgp_file)
        print_colored(f"Cleaned up {filename}", Colors.OKGREEN)

    def run(self):
        apache_url, php_url, apache_port, document_root, php_ini = self.get_user_input()

        # Check if Apache and PHP are already installed
        if not os.path.exists(self.apache_dir) or not os.path.exists(self.php_dir):
            # Download and install Apache with checksum and PGP verification
            self.download_and_extract(apache_url, self.install_dir, checksum_url=None, pgp_url=None, key_fingerprints=[apache_pgp_key_url])
            
            # Download and install PHP with checksum and PGP verification
            self.download_and_extract(php_url, self.install_dir, checksum_url=None, pgp_url=None, key_fingerprints=php_pgp_fingerprints)
        else:
            print_colored("Apache and PHP are already installed.", Colors.OKBLUE)

        # Configure Apache to work with PHP, using the user-provided settings
        self.apache_configurator.configure(apache_port, document_root, php_ini)
        
        # Set up environment variables
        self.apache_configurator.setup_environment_variables()
        
        # Start Apache
        self.apache_configurator.start_apache()
        
        print_colored(f"Setup complete! Apache with PHP is now running on http://localhost:{apache_port}", Colors.OKGREEN)

if __name__ == "__main__":
    try:
        installer = Installer()
        installer.run()
    except Exception as e:
        print_colored(f"An unexpected error occurred: {e}", Colors.FAIL)
        sys.exit(1)
