import os
import tkinter as tk
from tkinter import filedialog
from pyzbar.pyzbar import decode, ZBarSymbol
from PIL import Image
import shutil

def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder with Product Images")
    return folder_path

def convert_to_ean13(barcode_data):
    """Process barcode: strip the last digit and pad to 13 digits if needed"""
    if not barcode_data.isdigit():
        print(f"Debug: Barcode data is not a digit: {barcode_data}")
        return None
    
    # Strip the last digit
    barcode_stripped = barcode_data[:-1]
    print(f"Debug: Stripped barcode: {barcode_stripped}")
    
    # Pad to 13 digits if shorter
    barcode_padded = barcode_stripped.zfill(13)
    print(f"Debug: Padded barcode: {barcode_padded}")
    
    return barcode_padded

def infer_type_from_data(barcode_data):
    """Infer barcode type from data"""
    if not barcode_data.isdigit():
        return "Unknown"
    length = len(barcode_data)
    if length == 13 and int(barcode_data[1]) > 0:
        return "EAN13"
    elif length == 12 or (length == 13 and int(barcode_data[1]) == 0):
        return "UPC-A"
    return "Unknown"

def detect_barcode(image_path):
    """Detect barcode using pyzbar, ignoring QR codes"""
    try:
        with Image.open(image_path) as img:  # Auto-close image
            barcodes = decode(img)
            if barcodes:
                for barcode in barcodes:
                    if barcode.type != ZBarSymbol.QRCODE:  # Ignore QR codes
                        barcode_data = barcode.data.decode('utf-8')
                        barcode_type = barcode.type
                        print(f"Debug: Raw barcode detected in {image_path}: {barcode_data} (Type: {barcode_type})")
                        if barcode_data.isdigit():
                            ean13 = convert_to_ean13(barcode_data)
                            if ean13 and len(ean13) == 13:
                                print(f"Debug: Processed barcode: {ean13}")
                                return ean13, barcode_type, barcode_data
                print(f"Debug: No valid barcode (only QR codes or invalid) detected in {image_path}")
            else:
                print(f"Debug: No barcode detected in {image_path}")
            return None, None, None
    except Exception as e:
        print(f"Error detecting barcode in {image_path}: {str(e)}")
        return None, None, None

def process_images(folder_path):
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    
    # Create Not_detectable subfolder in the root folder if it doesn't exist
    not_detectable_folder = os.path.join(folder_path, "Not_detectable")
    os.makedirs(not_detectable_folder, exist_ok=True)
    
    # Track renamed files and their new names
    renamed_files = set()
    renamed_files_map = {}  # Maps original filename to new filename
    undetected_files = []
    
    # Walk through all directories and subdirectories
    for root, _, files in os.walk(folder_path):
        # Skip the Not_detectable folder
        if root == not_detectable_folder:
            continue
            
        # Filter and sort image files in the current directory
        image_files = [f for f in files if f.lower().endswith(image_extensions)]
        image_files = sorted(image_files)
        
        # Process files in the current directory
        for i, filename in enumerate(image_files):
            print(f"Debug: Processing file: {filename} in {root}")
            if filename in renamed_files:
                print(f"Debug: Skipping already renamed file: {filename}")
                continue
            
            full_path = os.path.join(root, filename)
            
            barcode, barcode_type, raw_barcode = detect_barcode(full_path)
            
            if barcode:
                if i > 0:
                    prev_filename = image_files[i-1]
                    prev_full_path = os.path.join(root, prev_filename)
                    prev_base_name = os.path.splitext(prev_filename)[0]
                    print(f"Debug: Comparing prev_base_name: {prev_base_name} with processed barcode: {barcode}")
                    
                    prev_new_name = renamed_files_map.get(prev_filename)
                    if prev_filename not in renamed_files and prev_base_name != barcode:
                        # Previous picture not renamed and doesn't match barcode, rename both
                        prev_ext = os.path.splitext(prev_filename)[1]
                        curr_ext = os.path.splitext(filename)[1]
                        new_prev_name = f"{barcode}{prev_ext}"
                        new_curr_name = f"back_{barcode}{curr_ext}"
                        try:
                            print(f"Debug: Renaming {prev_filename} to {new_prev_name}")
                            print(f"Debug: Renaming {filename} to {new_curr_name}")
                            os.rename(prev_full_path, os.path.join(root, new_prev_name))
                            os.rename(full_path, os.path.join(root, new_curr_name))
                            renamed_files.add(prev_filename)
                            renamed_files.add(filename)
                            renamed_files_map[prev_filename] = new_prev_name
                            renamed_files_map[filename] = new_curr_name
                            print(f"Renamed front image: {prev_filename} -> {new_prev_name}")
                            print(f"Renamed back image: {filename} -> {new_curr_name} "
                                  f"(Barcode Type: {barcode_type}, Raw Data: {raw_barcode})")
                        except OSError as e:
                            print(f"Error renaming files: {str(e)}")
                    else:
                        # Previous picture renamed or matches barcode, rename current without "back_"
                        curr_ext = os.path.splitext(filename)[1]
                        new_curr_name = f"{barcode}{curr_ext}"
                        try:
                            print(f"Debug: Renaming {filename} to {new_curr_name} "
                                  f"(previous file renamed to {prev_new_name or prev_filename} or matches barcode)")
                            os.rename(full_path, os.path.join(root, new_curr_name))
                            renamed_files.add(filename)
                            renamed_files_map[filename] = new_curr_name
                            print(f"Renamed image: {filename} -> {new_curr_name} "
                                  f"(Barcode Type: {barcode_type}, Raw Data: {raw_barcode})")
                        except OSError as e:
                            print(f"Error renaming file: {str(e)}")
                else:
                    # First image with barcode, rename without "back_" prefix
                    curr_ext = os.path.splitext(filename)[1]
                    new_curr_name = f"{barcode}{curr_ext}"
                    try:
                        print(f"Debug: Renaming {filename} to {new_curr_name} (first image with barcode)")
                        os.rename(full_path, os.path.join(root, new_curr_name))
                        renamed_files.add(filename)
                        renamed_files_map[filename] = new_curr_name
                        print(f"Renamed image: {filename} -> {new_curr_name} "
                              f"(Barcode Type: {barcode_type}, Raw Data: {raw_barcode})")
                    except OSError as e:
                        print(f"Error renaming file: {str(e)}")
            else:
                # Add to undetected list instead of moving immediately
                base_name = os.path.splitext(filename)[0]
                if base_name.isdigit() and len(base_name) in [12, 13]:
                    inferred_type = infer_type_from_data(base_name)
                    print(f"No barcode found in: {filename} after all attempts "
                          f"(Inferred Type from filename: {inferred_type})")
                else:
                    print(f"No barcode found in: {filename} after all attempts")
                undetected_files.append((root, filename))
    
    # Second pass: Move undetected files starting with a letter to Not_detectable
    if undetected_files:
        print(f"Debug: Checking {len(undetected_files)} undetected files for moving to Not_detectable folder")
        for root, filename in undetected_files:
            # Only move files starting with a letter
            if filename[0].isalpha():
                full_path = os.path.join(root, filename)
                new_path = os.path.join(not_detectable_folder, filename)
                try:
                    os.rename(full_path, new_path)
                    print(f"Moved {filename} from {root} to {new_path} (Not_detectable folder)")
                except OSError as e:
                    print(f"Error moving file {filename} to Not_detectable folder: {str(e)}")
            else:
                print(f"Debug: Keeping {filename} in place (starts with a number) in {root}")
    else:
        print("Debug: All files were renamed, no files to move to Not_detectable")

def main():
    print("Please select a folder containing the product images...")
    folder_path = select_folder()
    
    if not folder_path:
        print("No folder selected. Exiting...")
        return
    
    print(f"Processing images in: {folder_path}")
    
    try:
        process_images(folder_path)
        print("Image processing completed successfully!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    required = {'PIL': 'Pillow', 'pyzbar': 'pyzbar'}
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            print(f"Required package {package} is not installed.")
            print(f"Install it using: pip install {package}")
            exit(1)
    
    main()
