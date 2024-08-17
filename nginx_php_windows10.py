import os
import subprocess
import urllib.request
import zipfile
import shutil
import sys
import hashlib
import requests
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# Windows Apache and PHP Installer Script (Requires Python 3)
# -----------------------------------------------------------------------------
# This script automates the installation and configuration of Apache HTTP Server 
# and PHP on a Windows operating system. It provides a command-line interface 
# for entering all necessary information upfront and then configures Apache and 
# PHP according to the user's input. The script is compatible with Windows 10 
# and Windows Server environments.
#
# This script requires Python 3.x to be installed on your system.
#
# Features:
# - Option to manually provide download URLs or automatically scrape them
# - Verifies downloaded files using SHA256 checksums
# - Configures Apache to listen on a user-specified port
# - Integrates PHP with Apache
# - Sets up environment variables for Apache and PHP
# - Starts Apache as a Windows service
#
# Requirements:
# - Windows 10 or Windows Server
# - Administrator privileges
# - Python 3.x
#
# Usage:
# 1. Ensure Python 3.x is installed on your system.
# 2. Open Command Prompt as Administrator.
# 3. Run this script using Python 3: python3 setup_apache_php_windows.py
# 4. Enter the requested configuration details when prompted.
# -----------------------------------------------------------------------------

# Default URLs for Apache and PHP downloads
default_apache_url = "https://www.apachelounge.com/download/VS17/binaries/httpd-2.4.62-240718-win64-VS17.zip"
default_php_url = "https://windows.php.net/downloads/releases/php-8.2.22-Win32-vs16-x64.zip"

# Function to scrape the latest download URLs
def get_apache_download_url():
    url = "https://www.apachelounge.com/download/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    download_link = soup.find("a", href=True, text=lambda x: x and "httpd-2.4" in x and "win64-VS17.zip" in x)['href']
    checksum_link = download_link + ".txt"
    
    return download_link, checksum_link

def get_php_download_url():
    url = "https://windows.php.net/download/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    download_link = soup.find("a", href=True, text=lambda x: x and "php-8.2" in x and "Win32-vs16-x64.zip" in x)['href']
    checksum_link = "https://windows.php.net/downloads/releases/sha256sum.txt"
    
    return download_link, checksum_link

# Function to display the command-line interface and collect user input
def get_user_input():
    print("Windows Apache and PHP Installer")
    print("================================")
    
    use_default_urls = input("Use default URLs for Apache and PHP? (y/n, default is 'y'): ") or "y"
    
    if use_default_urls.lower() == "y":
        apache_url, php_url = default_apache_url, default_php_url
    else:
        apache_url = input(f"Enter the download URL for Apache (default is {default_apache_url}): ") or default_apache_url
        php_url = input(f"Enter the download URL for PHP (default is {default_php_url}): ") or default_php_url
    
    apache_port = input("Enter the port for Apache to listen on (default is 8080): ") or "8080"
    document_root = input(f"Enter the DocumentRoot path for Apache (default is {os.path.join(apache_dir, 'htdocs')}): ") or os.path.join(apache_dir, 'htdocs')
    php_ini = input(f"Enter the path to php.ini (leave blank to use default in PHP directory): ") or os.path.join(php_dir, "php.ini")
    
    return apache_url, php_url, apache_port, document_root, php_ini

def download_file(url, dest):
    """Download a file from a URL."""
    try:
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, dest)
        print(f"Downloaded to {dest}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: {url} not found (404). Attempting to scrape for latest download link...")
            if "httpd" in url:
                url, checksum_url = get_apache_download_url()
            elif "php" in url:
                url, checksum_url = get_php_download_url()
            print(f"Scraped URL: {url}")
            print(f"Scraped Checksum URL: {checksum_url}")
            download_file(url, dest)
        else:
            raise

def verify_checksum(file_path, expected_checksum):
    """Verify the SHA256 checksum of a downloaded file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    calculated_checksum = sha256.hexdigest()
    return calculated_checksum == expected_checksum

def download_and_extract(url, extract_to, checksum_url=None):
    """Download and extract a zip file from a URL."""
    filename = os.path.join(download_dir, os.path.basename(url))
    
    # Download the file
    download_file(url, filename)
    
    # Verify download if checksum URL is provided
    if checksum_url:
        print("Verifying checksum...")
        checksum_file = os.path.join(download_dir, os.path.basename(checksum_url))
        download_file(checksum_url, checksum_file)
        
        expected_checksum = None
        with open(checksum_file, "r") as f:
            for line in f:
                if os.path.basename(url) in line:
                    expected_checksum = line.split()[0]
                    break
        
        if expected_checksum is None:
            print(f"Error: Checksum for {os.path.basename(url)} not found.")
            sys.exit(1)
        
        if not verify_checksum(filename, expected_checksum):
            print(f"Error: Checksum verification failed for {filename}.")
            sys.exit(1)
        
        print("Checksum verified.")
    
    # Extract file
    print(f"Extracting {filename}...")
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    print(f"Extracted to {extract_to}")
    
    # Clean up downloaded file and checksum file
    os.remove(filename)
    if checksum_url:
        os.remove(checksum_file)
    print(f"Cleaned up {filename}")

def configure_apache_for_php(apache_port, document_root, php_ini):
    """Configure Apache to work with PHP and use the specified settings."""
    httpd_conf = os.path.join(apache_dir, "conf", "httpd.conf")
    
    # Backup the original httpd.conf
    shutil.copyfile(httpd_conf, f"{httpd_conf}.backup")

    # Update httpd.conf with user-specified port, DocumentRoot, and PHP configuration
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
        conf_file.write("\n# PHP Configuration\n")
        conf_file.write(f"LoadModule php_module \"{php_dir}\\php8apache2_4.dll\"\n")
        conf_file.write(f"AddHandler application/x-httpd-php .php\n")
        conf_file.write(f"PHPIniDir \"{os.path.dirname(php_ini)}\"\n")
        conf_file.write("DirectoryIndex index.php index.html\n")

    print(f"Apache configured to use PHP, listen on port {apache_port}, and serve content from {document_root}.")

def setup_environment_variables():
    """Set up system environment variables for Apache and PHP."""
    apache_bin_dir = os.path.join(apache_dir, "bin")
    php_bin_dir = php_dir

    current_path = os.environ["PATH"]
    
    if apache_bin_dir not in current_path:
        # Add Apache to the PATH
        os.environ["PATH"] = f"{apache_bin_dir};" + os.environ["PATH"]
        print("Apache added to PATH.")

    if php_bin_dir not in current_path:
        # Add PHP to the PATH
        os.environ["PATH"] = f"{php_bin_dir};" + os.environ["PATH"]
        print("PHP added to PATH.")

def start_apache():
    """Start Apache HTTP Server."""
    apache_exe = os.path.join(apache_dir, "bin", "httpd.exe")
    try:
        subprocess.run([apache_exe, "-k", "install"], check=True)
        subprocess.run([apache_exe, "-k", "start"], check=True)
        print("Apache HTTP Server started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start Apache: {e}")
        sys.exit(1)

def main():
    # Get user input for configuration
    apache_url, php_url, apache_port, document_root, php_ini = get_user_input()

    # Check if Apache and PHP are already installed
    if not os.path.exists(apache_dir) or not os.path.exists(php_dir):
        # Download and install Apache with checksum verification
        download_and_extract(apache_url, install_dir)
        
        # Download and install PHP with checksum verification
        download_and_extract(php_url, install_dir)
    else:
        print("Apache and PHP are already installed.")

    # Configure Apache to work with PHP, using the user-provided settings
    configure_apache_for_php(apache_port, document_root, php_ini)
    
    # Set up environment variables
    setup_environment_variables()
    
    # Start Apache
    start_apache()
    
    print(f"Setup complete! Apache with PHP is now running on http://localhost:{apache_port}")

if __name__ == "__main__":
    main()
