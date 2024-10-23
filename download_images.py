import argparse
import os
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import io

Image.MAX_IMAGE_PIXELS = None

def download_and_convert_file(url, base_output_dir, max_size=2048, quality=95):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        relative_path = url.split("events/", 1)[1] if "events/" in url else urlparse(url).path.lstrip('/')
        path_components = relative_path.split('/')
        
        event_name = path_components[0]
        location = '_'.join(path_components[1:4])
        filename = '_'.join(path_components[4:])
        filename = os.path.splitext(filename)[0] + '.jpg'
        
        output_dir = os.path.join(base_output_dir, "images", event_name, location)
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        # Open the image directly from the response content
        with Image.open(io.BytesIO(response.content)) as img:
            # Convert to RGB if it's not already
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize the image
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            
            # Save as JPEG
            img.save(filepath, 'JPEG', quality=quality)
        
        print(f"Downloaded and converted: {filepath}")
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Download and convert images from a list of URLs.")
    parser.add_argument("-l", "--links", required=True, help="Path to the text file containing URLs")
    parser.add_argument("-o", "--output", help="Path to the directory where images will be downloaded")
    parser.add_argument("-s", "--size", type=int, default=2048, help="Maximum size of the longest edge of the image (default: 2048)")
    parser.add_argument("-q", "--quality", type=int, default=95, help="JPEG quality (0-100, default: 95)")
    args = parser.parse_args()

    base_output_dir = args.output if args.output else os.path.dirname(os.path.abspath(__file__))

    with open(args.links, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_and_convert_file, url, base_output_dir, args.size, args.quality) for url in urls]
        for future in as_completed(futures):
            future.result()

    print(f"All downloads and conversions completed. Files saved in: {os.path.join(base_output_dir, 'images')}")

if __name__ == "__main__":
    main()