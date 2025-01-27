import requests
import random
import os
from tqdm import tqdm

# Base URL
base_url = "https://s3.amazonaws.com/google-landmark/train/images_{}.tar"

# Folder structure
base_folder = "TestData"
sub_folder = "GoogleLandMarkDT"
save_path = os.path.join(base_folder, sub_folder)

# Ensure the folders exist
os.makedirs(save_path, exist_ok=True)


def generate_random_link():
    """Generates a random URL by replacing {} with a random number (000-200)."""
    random_number = f"{random.randint(0, 200):03d}"  # Generate a number with leading zeros
    return base_url.format(random_number)


def download_file(url):
    """Downloads the file from the given URL with a progress bar."""
    local_filename = url.split("/")[-1]
    file_path = os.path.join(save_path, local_filename)

    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(file_path, "wb") as f, tqdm(
                desc=local_filename,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
    print(f"\nDownloaded: {file_path}")


while True:
    url = generate_random_link()
    print(f"Link to process: {url}")
    print("Options:\n1: Download this file\n2: Try another tar folder\n0: Exit")
    choice = input("Enter your choice (0/1/2): ").strip()

    if choice == "1":
        try:
            download_file(url)
        except Exception as e:
            print(f"Failed to download {url}. Error: {e}")
    elif choice == "2":
        print("Generating a new link...")
    elif choice == "0":
        print("Exiting program. Goodbye!")
        break
    else:
        print("Invalid input. Please enter 0, 1, or 2.")
