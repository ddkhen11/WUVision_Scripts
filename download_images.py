import argparse
import os
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

BASE_URL = "https://maxar-opendata.s3.us-west-2.amazonaws.com/events/"

def download_file(url, base_output_dir):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        relative_path = url.split(BASE_URL, 1)[1] if BASE_URL in url else urlparse(url).path.lstrip('/')

        path_components = relative_path.split('/')
        
        event_name = path_components[0]
        location = '_'.join(path_components[1:4])  # Combine ard/XX/XXXXXXXXXX into ard_XX_XXXXXXXXXX
        filename = '_'.join(path_components[4:])
        
        # Create the full output path
        output_dir = os.path.join(base_output_dir, "images", event_name, location)
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"Downloaded: {filepath}")
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Download images from a list of URLs.")
    parser.add_argument("-l", "--links", required=True, help="Path to the text file containing URLs")
    parser.add_argument("-o", "--output", help="Path to the directory where images will be downloaded")
    args = parser.parse_args()

    base_output_dir = args.output if args.output else os.path.dirname(os.path.abspath(__file__))

    with open(args.links, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_file, url, base_output_dir) for url in urls]
        for future in as_completed(futures):
            future.result()

    print(f"All downloads completed. Files saved in: {os.path.join(base_output_dir, 'images')}")

if __name__ == "__main__":
    main()