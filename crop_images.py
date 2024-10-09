import argparse
import os
import random
from PIL import Image
import re
import torch
import numpy as np

# Remove PIL image size limit to handle large satellite images
Image.MAX_IMAGE_PIXELS = None

def get_random_bounding_box(size, res):
    """
    Generate a random bounding box.
    
    Args:
    size: Tuple of (height, width) of the image
    res: Tuple of (height, width) of the desired crop size
    
    Returns:
    Tuple of (minx, maxx, miny, maxy) in normalized coordinates
    """
    height, width = size
    res_height, res_width = res
    
    max_x = width - res_width
    max_y = height - res_height
    
    x = random.randint(0, max(0, max_x))
    y = random.randint(0, max(0, max_y))
    
    minx, maxx = x / width, (x + res_width) / width
    miny, maxy = y / height, (y + res_height) / height
    
    return (minx, maxx, miny, maxy)

def bbox_to_yx_np(bbox, size):
    """
    Convert a bounding box from normalized coordinates to pixel coordinates.
    
    Args:
    bbox: Tuple of (minx, maxx, miny, maxy) in normalized coordinates
    size: Tuple of (height, width) of the image
    
    Returns:
    Tuple of (top, left, bottom, right) in pixel coordinates
    """
    height, width = size
    minx, maxx, miny, maxy = bbox
    return (
        int(miny * height),
        int(minx * width),
        int(maxy * height),
        int(maxx * width)
    )

def get_image_pairs(disaster_folder, location_folder):
    """
    Find and return pairs of before/after images for a specific disaster and location.
    """
    base_path = os.path.join('images', disaster_folder, location_folder)
    files = os.listdir(base_path)
    
    # Sort files by date
    dated_files = []
    for file in files:
        # Use regex to extract date from filename
        match = re.match(r'(\d{4}-\d{2}-\d{2})_(.+)', file)
        if match:
            date_str, _ = match.groups()
            dated_files.append((date_str, file))
    
    dated_files.sort(key=lambda x: x[0])  # Sort by date string
    
    # Find pair of images (before and after)
    if len(dated_files) >= 2:
        before_file = dated_files[0][1]  # Earliest date
        after_file = dated_files[-1][1]  # Latest date
        return [(os.path.join(base_path, before_file),
                 os.path.join(base_path, after_file))]
    
    return []

def get_next_pair_number(output_base):
    """
    Determine the next available pair number for naming the output folder.
    """
    existing_pairs = [d for d in os.listdir(output_base) if d.startswith('pair_') and os.path.isdir(os.path.join(output_base, d))]
    if not existing_pairs:
        return 1
    pair_numbers = [int(d.split('_')[1]) for d in existing_pairs]
    return max(pair_numbers) + 1

def is_valid_crop(image, bbox, threshold=0.01):
    """
    Check if the crop is not mostly black.
    
    Args:
    image: PIL Image object
    bbox: Tuple of (left, top, right, bottom)
    threshold: Minimum proportion of non-black pixels required
    
    Returns:
    Boolean indicating if the crop is valid
    """
    crop = image.crop(bbox)
    crop_array = torch.tensor(np.array(crop)).float() / 255
    non_black_pixels = torch.sum(crop_array > 0.1)  # Count pixels brighter than 10% intensity
    total_pixels = crop_array.numel() / 3  # Divide by 3 for RGB channels
    return (non_black_pixels / total_pixels) > threshold

def crop_image_pair(before_path, after_path, output_base, crop_size=256, max_attempts=100):
    """
    Crop a pair of before/after images and save the crops.
    
    Args:
    before_path: Path to the 'before' image
    after_path: Path to the 'after' image
    output_base: Base directory for saving cropped images
    crop_size: Size of the square crop
    max_attempts: Maximum number of attempts to find a valid crop
    
    Returns:
    Path to the output folder if successful, None otherwise
    """
    try:
        with Image.open(before_path) as before_img, Image.open(after_path) as after_img:
            width, height = before_img.size
            
            for _ in range(max_attempts):
                # Get a random bounding box
                bbox = get_random_bounding_box((height, width), (crop_size, crop_size))
                top, left, bottom, right = bbox_to_yx_np(bbox, (height, width))
                
                # Check if the crop is valid for both images
                if is_valid_crop(before_img, (left, top, right, bottom)) and is_valid_crop(after_img, (left, top, right, bottom)):
                    before_crop = before_img.crop((left, top, right, bottom))
                    after_crop = after_img.crop((left, top, right, bottom))
                    
                    # Create output folder
                    pair_number = get_next_pair_number(output_base)
                    output_folder = os.path.join(output_base, f'pair_{pair_number}')
                    os.makedirs(output_folder, exist_ok=True)
                    
                    # Save cropped images
                    before_filename = os.path.basename(before_path)
                    after_filename = os.path.basename(after_path)
                    before_crop.save(os.path.join(output_folder, f'before_{before_filename}'))
                    after_crop.save(os.path.join(output_folder, f'after_{after_filename}'))
                    
                    print(f"Successfully cropped and saved images in {output_folder}.")
                    return output_folder
            
            print("Failed to find a valid crop after maximum attempts.")
            return None
    except Exception as e:
        print(f"Error processing images: {e}")
        return None

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Crop a pair of images from before and after an event.")
    parser.add_argument("-d", "--disaster", required=True, help="Name of the disaster folder")
    parser.add_argument("-l", "--location", required=True, help="Name of the location folder")
    parser.add_argument("-s", "--size", type=int, default=256, help="Size of the square crop in pixels")
    args = parser.parse_args()

    # Get image pair
    pairs = get_image_pairs(args.disaster, args.location)
    
    if not pairs:
        print("No suitable image pair found.")
        return

    # Create output folder
    output_base = os.path.join('cropped_images', args.disaster, args.location)
    os.makedirs(output_base, exist_ok=True)

    # Crop and save the pair
    before_path, after_path = pairs[0]
    output_folder = crop_image_pair(before_path, after_path, output_base, args.size)

    if output_folder:
        print(f"Processing completed. Results saved in: {output_folder}")
    else:
        print("Processing failed.")

if __name__ == "__main__":
    main()