# WUVision_Scripts

1. `download_images.py`: Downloads satellite images from specified URLs.
2. `crop_images.py`: Crops a pair of before/after images from a specified disaster event and location.

## Requirements

- Python 3.x
- Required Python packages:
  - requests
  - Pillow (PIL)

You can install the required packages using pip:

```
pip install requests Pillow
```

## Usage

### 1. download_images.py

This script downloads satellite images from a list of URLs provided in a text file.

```
python download_images.py -l <PATH_TO_URL_LIST> [-o <OUTPUT_DIRECTORY>]
```

- `-l` or `--links`: Path to a text file containing image URLs (one URL per line)
- `-o` or `--output`: (Optional) Path to the directory where images will be downloaded. If not specified, images will be saved in the current directory.

Example:
```
python download_images.py -l image_urls.txt -o /path/to/output
```

### 2. crop_images.py

This script crops a pair of before/after images from a specified disaster event and location.

```
python crop_images.py -d <DISASTER_FOLDER> -l <LOCATION_FOLDER> [-s <CROP_SIZE>]
```

- `-d` or `--disaster`: Name of the disaster folder
- `-l` or `--location`: Name of the location folder
- `-s` or `--size`: (Optional) Size of the square crop in pixels (default is 256)

Example:
```
python crop_images.py -d New-Zealand-Flooding23 -l ard_60_213311212303 -s 512
```

## Output Structure

- `download_images.py` saves files in: `<output_directory>/images/<event_name>/<location>/<filename>`
- `crop_images.py` saves cropped images in: `cropped_images/<disaster_name>/<location>/pair_<number>/before_<filename>` and `after_<filename>`

## Notes

- The `download_images.py` script uses multithreading to download multiple images concurrently.
- The `crop_images.py` script selects the earliest and latest images in the specified folder for cropping.
- Large images are handled by setting `Image.MAX_IMAGE_PIXELS = None` in the crop script. Use caution with untrusted image sources.