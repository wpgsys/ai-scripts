#MacOS script to verify any ubuntu .iso file with ease... shit be annoying af doe? :D

import hashlib
import requests
import sys
import os
import re
import subprocess

# Base URL templates for official Ubuntu releases
BASE_URL = "https://releases.ubuntu.com/{version}/SHA256SUMS"
GPG_URL = "https://releases.ubuntu.com/{version}/SHA256SUMS.gpg"

# Ubuntu official GPG key IDs
UBUNTU_GPG_KEYS = [
    "0xFBB75451",   # Older Ubuntu releases
    "0xD94AA3F0EFE21092"  # Newer Ubuntu releases (like 22.04.2)
]

def calculate_local_checksum(file_path):
    """Calculate SHA256 checksum of the given ISO file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks of 4MB
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error calculating checksum: {e}")
        sys.exit(1)

def extract_ubuntu_version(file_name):
    """Extract the Ubuntu version (including sub-versions) from the ISO filename."""
    # Match for version formats like 22.04, 22.04.1, 22.04.2, etc.
    match = re.search(r"ubuntu-(\d{2}\.\d{2}(?:\.\d+)?)-", file_name)
    if match:
        return match.group(1)  # Example: '22.04', '22.04.1', '22.04.2'
    else:
        print("Error: Unable to extract Ubuntu version from filename.")
        sys.exit(1)

def download_file(url, local_filename):
    """Download a file from the given URL."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {local_filename}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        sys.exit(1)

def import_gpg_keys():
    """Import all necessary Ubuntu GPG keys for verification."""
    for key in UBUNTU_GPG_KEYS:
        try:
            # Import the GPG key if not already imported
            subprocess.run(["gpg", "--keyserver", "keyserver.ubuntu.com", "--recv-keys", key], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error importing GPG key {key}: {e}")
            sys.exit(1)

def verify_gpg_signature(checksum_file, gpg_file):
    """Verify the GPG signature of the checksum file."""
    try:
        # Import necessary GPG keys
        import_gpg_keys()

        # Verify the checksum file using its GPG signature
        result = subprocess.run(["gpg", "--verify", gpg_file, checksum_file], capture_output=True, text=True)
        if result.returncode == 0:
            print("GPG signature is valid.")
        else:
            print("GPG signature verification failed!")
            print(result.stderr)
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error during GPG verification: {e}")
        sys.exit(1)

def fetch_and_verify_checksums(version):
    """Fetch checksums and their GPG signature, and verify the signature."""
    checksum_url = BASE_URL.format(version=version)
    gpg_url = GPG_URL.format(version=version)
    checksum_file = "SHA256SUMS"
    gpg_file = "SHA256SUMS.gpg"

    # Download checksum file and GPG signature file
    download_file(checksum_url, checksum_file)
    download_file(gpg_url, gpg_file)

    # Verify the checksum file using GPG
    verify_gpg_signature(checksum_file, gpg_file)

    # Return the list of checksums
    with open(checksum_file, 'r') as f:
        return f.readlines()

def find_checksum_in_list(lines, iso_filename):
    """Find the checksum for the specific ISO filename in the list of checksums."""
    for line in lines:
        if iso_filename in line:
            return line.split()[0]  # The checksum should be the first element
    print(f"Error: Checksum for {iso_filename} not found in fetched checksums.")
    sys.exit(1)

def verify_checksum(local_checksum, remote_checksum):
    """Compare local checksum with the fetched remote checksum."""
    if local_checksum == remote_checksum:
        print(f"Checksum verification successful: {local_checksum}")
    else:
        print(f"Checksum mismatch! Local: {local_checksum}, Remote: {remote_checksum}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 verify.py <path_to_iso>")
        sys.exit(1)

    iso_file = sys.argv[1]

    if not os.path.isfile(iso_file):
        print(f"File '{iso_file}' does not exist.")
        sys.exit(1)

    iso_filename = os.path.basename(iso_file)
    print(f"Detected ISO file: {iso_filename}")

    print("Extracting Ubuntu version from filename...")
    ubuntu_version = extract_ubuntu_version(iso_filename)
    print(f"Detected Ubuntu version: {ubuntu_version}")

    print("Calculating local checksum for the ISO file...")
    local_checksum = calculate_local_checksum(iso_file)
    print(f"Local checksum: {local_checksum}")

    print(f"\nFetching and verifying remote checksums for Ubuntu {ubuntu_version}...")
    remote_checksum_list = fetch_and_verify_checksums(ubuntu_version)

    print("\nLooking for checksum matching the ISO file...")
    remote_checksum = find_checksum_in_list(remote_checksum_list, iso_filename)

    print("\nVerifying checksum...")
    verify_checksum(local_checksum, remote_checksum)

if __name__ == "__main__":
    main()
