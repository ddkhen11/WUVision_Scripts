import argparse
import subprocess
import os
import leafmap
import time
from multiprocessing import Pool, cpu_count
import multiprocessing
from functools import partial
from datetime import datetime
import sys

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

def run_get_all_valid_tiles(disaster, location, crop_size):
    """Run get_all_valid_tiles.py for a specific disaster and location."""
    try:
        print(f"\nProcessing tiles for disaster: {disaster}, location: {location}")
        subprocess.run([
            'python',
            'get_all_valid_tiles.py',
            '-d', disaster,
            '-l', location,
            '-s', str(crop_size)
        ], check=True)
        return location, True
    except subprocess.CalledProcessError as e:
        print(f"Error processing tiles for {location}: {e}")
        return location, False

def get_locations_for_disaster(disaster):
    """Get all location folders for a specific disaster."""
    disaster_path = os.path.join('images', disaster)
    if not os.path.exists(disaster_path):
        print(f"No image directory found for disaster: {disaster}")
        return []
    return [d for d in os.listdir(disaster_path) if os.path.isdir(os.path.join(disaster_path, d))]

def process_locations_parallel(disaster, locations, crop_size, max_workers=None):
    """Process all locations for a disaster in parallel."""
    if not max_workers:
        max_workers = max(1, cpu_count() - 1)
    
    print(f"Processing {len(locations)} locations for {disaster} using {max_workers} workers")
    
    with Pool(processes=max_workers) as pool:
        process_func = partial(run_get_all_valid_tiles, disaster, crop_size=crop_size)
        results = pool.map(process_func, locations)
    
    return results

def process_disaster(disaster, crop_size, max_workers=None):
    """Process a complete disaster workflow."""
    start_time = datetime.now()
    print(f"\n{'='*80}")
    print(f"Processing disaster: {disaster}")
    print(f"Start time: {start_time}")
    print(f"{'='*80}")
    
    try:
        # Step 1: Get valid links
        links_file = os.path.join('filtered_links', f"{disaster}_filtered_images.txt")
        if not os.path.exists(links_file):
            if not run_get_valid_links(disaster):
                print(f"Failed to get valid links for {disaster}")
                return disaster, False
        else:
            print(f"Using existing links file: {links_file}")
        
        # Step 2: Download images
        if not run_download_images(links_file, os.getcwd()):
            print(f"Failed to download images for {disaster}")
            return disaster, False
        
        # Step 3: Process locations in parallel
        locations = get_locations_for_disaster(disaster)
        if not locations:
            print(f"No locations found for {disaster}")
            return disaster, False
        
        results = process_locations_parallel(disaster, locations, crop_size, max_workers)
        
        # Process results
        successful_locations = sum(1 for _, success in results if success)
        print(f"\nProcessed {successful_locations}/{len(locations)} locations successfully for {disaster}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"Duration: {duration}")
        
        return disaster, successful_locations > 0
        
    except Exception as e:
        print(f"Unexpected error processing disaster {disaster}: {e}")
        return disaster, False

def main():
    parser = argparse.ArgumentParser(description="Process multiple disasters end-to-end in parallel.")
    parser.add_argument("-d", "--disasters", nargs='+', help="List of disasters to process. If not specified, all available disasters will be processed.")
    parser.add_argument("-s", "--size", type=int, default=256, help="Size of the square crop in pixels")
    parser.add_argument("-w", "--workers", type=int, default=None, help="Number of worker processes to use. Defaults to CPU count - 1")
    parser.add_argument("-dw", "--disaster-workers", type=int, default=2, help="Number of disasters to process in parallel. Defaults to 2")
    args = parser.parse_args()

    # Configure maximum workers
    max_workers = args.workers if args.workers is not None else max(1, cpu_count() - 1)
    disaster_workers = min(args.disaster_workers, cpu_count())
    
    print(f"Using {disaster_workers} workers for disasters and up to {max_workers} workers for locations")
    
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

    # Process disasters in parallel
    process_func = partial(process_disaster, crop_size=args.size, max_workers=max_workers)
    
    overall_start_time = datetime.now()
    print(f"\nStarting overall processing at: {overall_start_time}")
    
    with Pool(processes=disaster_workers) as pool:
        results = pool.map(process_func, disasters_to_process)
    
    # Process results
    successful_disasters = sum(1 for _, success in results if success)
    print(f"\nProcessing completed!")
    print(f"Successfully processed {successful_disasters}/{len(disasters_to_process)} disasters")
    
    overall_end_time = datetime.now()
    overall_duration = overall_end_time - overall_start_time
    print(f"Total processing time: {overall_duration}")
    
    # Print detailed results
    print("\nDetailed results:")
    for disaster, success in results:
        status = "Success" if success else "Failed"
        print(f"{disaster}: {status}")

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()