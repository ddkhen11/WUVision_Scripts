import argparse
import subprocess
import os
import leafmap
import time
from multiprocessing import Pool, cpu_count
import multiprocessing
from datetime import datetime

def run_get_valid_links(disaster):
    """Run get_valid_links.py for a specific disaster."""
    print(f"\nGetting valid links for disaster: {disaster}")
    try:
        subprocess.run(['python', 'get_valid_links.py', '-d', disaster], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error getting links for {disaster}: {e}")
        return False

def run_download_images(links_file, output_dir):
    """Run download_images.py for a specific links file."""
    print(f"\nDownloading images from: {links_file}")
    try:
        subprocess.run([
            'python', 
            'download_images.py', 
            '-l', links_file,
            '-o', output_dir
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error downloading images: {e}")
        return False

def run_get_all_valid_tiles(args):
    """Run get_all_valid_tiles.py for a specific disaster and location."""
    disaster, location, crop_size = args
    try:
        print(f"\nProcessing tiles for disaster: {disaster}, location: {location}")
        subprocess.run([
            'python',
            'get_all_valid_tiles.py',
            '-d', disaster,
            '-l', location,
            '-s', str(crop_size)
        ], check=True)
        return (disaster, location, True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing tiles for {location}: {e}")
        return (disaster, location, False)

def get_locations_for_disaster(disaster):
    """Get all location folders for a specific disaster."""
    disaster_path = os.path.join('images', disaster)
    if not os.path.exists(disaster_path):
        print(f"No image directory found for disaster: {disaster}")
        return []
    return [d for d in os.listdir(disaster_path) if os.path.isdir(os.path.join(disaster_path, d))]

def check_disaster_downloaded(disaster):
    """Check if images for a disaster have already been downloaded."""
    # Normalize disaster name for comparison
    disaster = disaster.replace("-", "").lower()
    
    # Check all directories in images folder
    images_dir = 'images'
    if not os.path.exists(images_dir):
        return False
        
    existing_dirs = os.listdir(images_dir)
    
    # Normalize existing directory names for comparison
    for existing_dir in existing_dirs:
        if existing_dir.replace("-", "").lower() == disaster:
            disaster_path = os.path.join(images_dir, existing_dir)
            locations = [d for d in os.listdir(disaster_path) 
                        if os.path.isdir(os.path.join(disaster_path, d))]
            
            if locations:
                print(f"\nFound existing downloads for {existing_dir} with {len(locations)} locations")
                return True
    
    print(f"\nNo existing downloads found for {disaster}")
    return False

def process_disaster_sequential(disaster, crop_size):
    """Process a single disaster sequentially."""
    start_time = datetime.now()
    print(f"\n{'='*80}")
    print(f"Processing disaster: {disaster}")
    print(f"Start time: {start_time}")
    print(f"{'='*80}")
    
    try:
        # Check if already downloaded
        if not check_disaster_downloaded(disaster):
            # Step 1: Get valid links
            links_file = os.path.join('filtered_links', f"{disaster}_filtered_images.txt")
            if not os.path.exists(links_file):
                if not run_get_valid_links(disaster):
                    print(f"Failed to get valid links for {disaster}")
                    return []
            else:
                print(f"Using existing links file: {links_file}")
            
            # Step 2: Download images
            if not run_download_images(links_file, os.getcwd()):
                print(f"Failed to download images for {disaster}")
                return []
        else:
            print(f"Using existing downloads for {disaster}")
        
        # Step 3: Get locations
        locations = get_locations_for_disaster(disaster)
        if not locations:
            print(f"No locations found for {disaster}")
            return []
        
        # Return list of (disaster, location) tuples for parallel processing
        return [(disaster, loc, crop_size) for loc in locations]
        
    except Exception as e:
        print(f"Unexpected error processing disaster {disaster}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Process multiple disasters end-to-end in parallel.")
    parser.add_argument("-d", "--disasters", nargs='+', help="List of disasters to process. If not specified, all available disasters will be processed.")
    parser.add_argument("-s", "--size", type=int, default=256, help="Size of the square crop in pixels")
    parser.add_argument("-w", "--workers", type=int, default=None, help="Number of worker processes to use. Defaults to CPU count - 1")
    args = parser.parse_args()

    # Configure maximum workers
    max_workers = args.workers if args.workers is not None else max(1, cpu_count() - 1)
    
    print(f"Using {max_workers} worker processes")
    
    # Get list of disasters
    available_disasters = leafmap.maxar_collections()
    if args.disasters:
        disasters_to_process = [d for d in args.disasters if d in available_disasters]
        if not disasters_to_process:
            print("No valid disasters specified.")
            return
    else:
        disasters_to_process = available_disasters

    print(f"Will process the following disasters: {', '.join(disasters_to_process)}")
    time.sleep(3)  # Give user time to read the list

    overall_start_time = datetime.now()
    print(f"\nStarting overall processing at: {overall_start_time}")
    
    # Process each disaster sequentially, but locations in parallel
    all_location_tasks = []
    for disaster in disasters_to_process:
        location_tasks = process_disaster_sequential(disaster, args.size)
        all_location_tasks.extend(location_tasks)
    
    if not all_location_tasks:
        print("\nNo locations to process. Exiting.")
        return
        
    print(f"\nProcessing {len(all_location_tasks)} total locations across all disasters")
    
    # Process all locations in parallel
    successful_locations = 0
    with Pool(processes=max_workers) as pool:
        results = pool.map(run_get_all_valid_tiles, all_location_tasks)
        
        # Count successful locations
        successful_locations = sum(1 for _, _, success in results if success)
    
    overall_end_time = datetime.now()
    overall_duration = overall_end_time - overall_start_time
    
    # Print final results
    print("\nProcessing completed!")
    print(f"Successfully processed {successful_locations}/{len(all_location_tasks)} locations")
    print(f"Total processing time: {overall_duration}")
    
    # Print detailed results by disaster
    print("\nDetailed results by disaster:")
    disaster_results = {}
    for disaster, location, success in results:
        if disaster not in disaster_results:
            disaster_results[disaster] = {"total": 0, "success": 0}
        disaster_results[disaster]["total"] += 1
        if success:
            disaster_results[disaster]["success"] += 1
    
    for disaster, stats in disaster_results.items():
        print(f"{disaster}: {stats['success']}/{stats['total']} locations successful")

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()