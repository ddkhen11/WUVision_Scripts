import argparse
import os
import random
from PIL import Image
import re
Image.MAX_IMAGE_PIXELS = None  # Remove image size limit

def get_image_pairs(disaster_folder, location_folder):
    base_path = os.path.join('images', disaster_folder, location_folder)
    files = os.listdir(base_path)
    
    # Sort files by date
    dated_files = []
    for file in files:
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
    existing_pairs = [d for d in os.listdir(output_base) if d.startswith('pair_') and os.path.isdir(os.path.join(output_base, d))]
    if not existing_pairs:
        return 1
    pair_numbers = [int(d.split('_')[1]) for d in existing_pairs]
    return max(pair_numbers) + 1

def crop_image_pair(before_path, after_path, output_base, crop_size=256):
    try:
        with Image.open(before_path) as before_img, Image.open(after_path) as after_img:
            width, height = before_img.size
            left = random.randint(0, width - crop_size)
            top = random.randint(0, height - crop_size)
            
            before_crop = before_img.crop((left, top, left + crop_size, top + crop_size))
            after_crop = after_img.crop((left, top, left + crop_size, top + crop_size))
            
            # Get the next pair number and create the output folder
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
    except Exception as e:
        print(f"Error processing images: {e}")
        return None

def main():
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