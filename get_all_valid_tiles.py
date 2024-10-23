import argparse
import os
import numpy as np
from PIL import Image
import re
import torch

# Remove PIL image size limit to handle large satellite images
Image.MAX_IMAGE_PIXELS = None

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

def is_valid_crop(image, bbox, non_black_threshold=0.9):
    """
    Check if the crop is not mostly black or not mostly white (clouds).
    
    Args:
    image: PIL Image object
    bbox: Tuple of (left, top, right, bottom)
    non_black_threshold: Minimum proportion of non-black pixels required
    non_white_threshold: Minimum proportion of non-white pixels required
    
    Returns:
    Boolean indicating if the crop is valid
    """
    crop = image.crop(bbox)
    crop_array = torch.tensor(np.array(crop)).float() / 255
    non_black_pixels = torch.sum(crop_array > 0.1)  # Count pixels brighter than 10% intensity
    total_pixels = crop_array.numel() / 3  # Divide by 3 for RGB channels
    return (non_black_pixels / total_pixels) > non_black_threshold

def process_image_pair(before_path, after_path, output_base, crop_size=256):
    """
    Process a pair of before/after images, extracting all possible squares of the specified size
    and saving only the valid pairs.
    
    Args:
    before_path: Path to the 'before' image
    after_path: Path to the 'after' image
    output_base: Base directory for saving cropped images
    crop_size: Size of the square crop
    
    Returns:
    Number of valid crops saved
    """
    try:
        with Image.open(before_path) as before_img, Image.open(after_path) as after_img:
            width, height = before_img.size
            
            valid_crops = 0
            for y in range(0, height - crop_size + 1, crop_size):
                for x in range(0, width - crop_size + 1, crop_size):
                    bbox = (x, y, x + crop_size, y + crop_size)
                    
                    if is_valid_crop(before_img, bbox) and is_valid_crop(after_img, bbox):
                        before_crop = before_img.crop(bbox)
                        after_crop = after_img.crop(bbox)
                        
                        # Create output folder
                        output_folder = os.path.join(output_base, f'pair_{valid_crops}')
                        os.makedirs(output_folder, exist_ok=True)
                        
                        # Save cropped images
                        before_filename = os.path.basename(before_path)
                        after_filename = os.path.basename(after_path)
                        before_crop.save(os.path.join(output_folder, f'before_{before_filename}'))
                        after_crop.save(os.path.join(output_folder, f'after_{after_filename}'))
                        
                        valid_crops += 1
                        
                        if valid_crops % 100 == 0:
                            print(f"Processed {valid_crops} valid crops...")
            
            print(f"Total valid crops saved: {valid_crops}")
            return valid_crops
    except Exception as e:
        print(f"Error processing images: {e}")
        return 0

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Crop all valid squares from a pair of before/after event images.")
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

    # Process and save all valid crops from the pair
    before_path, after_path = pairs[0]
    total_crops = process_image_pair(before_path, after_path, output_base, args.size)

    if total_crops > 0:
        print(f"Processing completed. {total_crops} valid crops saved in: {output_base}")
    else:
        print("Processing failed or no valid crops found.")

if __name__ == "__main__":
    main()