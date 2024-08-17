import os
import subprocess
import urllib.request
import zipfile
import shutil


class MinerSetup:
    def __init__(self, wallet_address, etc_pool_url, monero_pool_url, cpu_threads=0):
        self.wallet_address = wallet_address
        self.etc_pool_url = etc_pool_url
        self.monero_pool_url = monero_pool_url
        self.cpu_threads = cpu_threads

    def download_file(self, url, destination):
        try:
            print(f"Downloading from {url}...")
            urllib.request.urlretrieve(url, destination)
            print(f"Downloaded {destination}.")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            raise

    def extract_file(self, file_path, extract_to):
        try:
            print(f"Extracting {file_path} to {extract_to}...")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            print(f"Extracted {file_path}.")
        except Exception as e:
            print(f"Error extracting {file_path}: {e}")
            raise

    def cleanup_file(self, file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed {file_path}.")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
            raise

    def download_trex(self):
        trex_url = "https://github.com/trexminer/T-Rex/releases/download/0.26.6/t-rex-0.26.6-win.zip"
        trex_zip_path = "t-rex.zip"
        self.download_file(trex_url, trex_zip_path)
        self.extract_file(trex_zip_path, "t-rex")
        self.cleanup_file(trex_zip_path)

    def download_xmrig(self):
        xmrig_url = "https://github.com/xmrig/xmrig/releases/download/v6.19.2/xmrig-6.19.2-msvc-win64.zip"
        xmrig_zip_path = "xmrig.zip"
        self.download_file(xmrig_url, xmrig_zip_path)
        self.extract_file(xmrig_zip_path, "xmrig")
        self.cleanup_file(xmrig_zip_path)

    def create_batch_file(self, filename, content):
        try:
            with open(filename, "w") as batch_file:
                batch_file.write(content)
            print(f"Created {filename}.")
        except Exception as e:
            print(f"Error creating {filename}: {e}")
            raise

    def create_mining_batch_files(self):
        gpu_batch_content = f"""
        @echo off
        :start
        t-rex\\t-rex.exe -a etchash -o {self.etc_pool_url} -u {self.wallet_address}.gpu_worker -p x
        goto start
        """
        self.create_batch_file("start_gpu_mining.bat", gpu_batch_content)

        cpu_batch_content = f"""
        @echo off
        :start
        xmrig\\xmrig.exe -o {self.monero_pool_url} -u {self.wallet_address} -p x -t {self.cpu_threads} --cpu-max-threads-hint 100
        goto start
        """
        self.create_batch_file("start_cpu_mining.bat", cpu_batch_content)

    def start_mining(self):
        try:
            print("Starting GPU mining...")
            subprocess.Popen(["start_gpu_mining.bat"], shell=True)
            print("Starting CPU mining...")
            subprocess.Popen(["start_cpu_mining.bat"], shell=True)
        except Exception as e:
            print(f"Error starting mining processes: {e}")
            raise

    def setup_mining(self):
        try:
            print("Setting up mining...")
            self.download_trex()
            self.download_xmrig()
            self.create_mining_batch_files()
            self.start_mining()
            print("Mining setup complete. Mining is now running at full power using both GPU and CPU.")
        except Exception as e:
            print(f"Setup failed: {e}")
            raise


if __name__ == "__main__":
    wallet_address = input("Enter your wallet address (for both ETC and Monero): ")
    etc_pool_url = input("Enter your Ethereum Classic mining pool URL (e.g., stratum+tcp://etc.2miners.com:1010): ")
    monero_pool_url = input("Enter your Monero mining pool URL (e.g., pool.minexmr.com:4444): ")
    cpu_threads = input("Enter the number of CPU threads to use (
