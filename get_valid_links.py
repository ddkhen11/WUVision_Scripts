import sys
import csv
import requests
import argparse
import os
from collections import defaultdict
import leafmap

def get_disaster_data(disaster_name):
    url = f"https://raw.githubusercontent.com/opengeos/maxar-open-data/master/datasets/{disaster_name}.tsv"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve data for disaster: {disaster_name}")
        sys.exit(1)
    return response.text.splitlines()

def filter_images(disaster_data):
    reader = csv.DictReader(disaster_data, delimiter='\t')
    
    valid_images = []
    quadkey_count = defaultdict(int)
    
    for row in reader:
        clouds_percent = float(row['tile:clouds_percent'])
        if clouds_percent <= 15:
            valid_images.append(row)
            quadkey_count[row['quadkey']] += 1
    
    filtered_images = [img for img in valid_images if quadkey_count[img['quadkey']] > 1]
    
    return [img['visual'] for img in filtered_images]

def save_links(links, disaster_name):
    folder_name = "filtered_links"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    filename = os.path.join(folder_name, f"{disaster_name}_filtered_images.txt")
    with open(filename, 'w') as f:
        for link in links:
            f.write(f"{link}\n")
    print(f"Filtered image links saved to {filename}")

def main(disaster_name):
    disaster_data = get_disaster_data(disaster_name)
    filtered_links = filter_images(disaster_data)
    save_links(filtered_links, disaster_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter and save image links for a specific disaster.")
    parser.add_argument("-d", "--disaster", required=True, help="Name of the disaster")
    args = parser.parse_args()

    disaster_name = args.disaster

    # Check if the disaster name is valid
    valid_disasters = leafmap.maxar_collections()
    if disaster_name not in valid_disasters:
        print(f"Error: '{disaster_name}' is not a valid disaster name.")
        print("Valid disaster names are:")
        for name in valid_disasters:
            print(f"  {name}")
        sys.exit(1)

    main(disaster_name)