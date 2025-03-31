import os
import tkinter as tk
from tkinter import filedialog
from pyzbar.pyzbar import decode
from PIL import Image

def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder with Product Images")
    return folder_path

def calculate_ean13_check_digit(barcode_12):
    """Calculate EAN-13 check digit for a 12-digit barcode (even positions * 3)"""
    if len(barcode_12) != 12 or not barcode_12.isdigit():
        return None
    even_sum = sum(int(barcode_12[i]) for i in range(1, 12, 2)) * 3  # Even positions * 3
    odd_sum = sum(int(barcode_12[i]) for i in range(0, 12, 2))       # Odd positions
    total = odd_sum + even_sum
    return str((10 - (total % 10)) % 10)

def convert_to_ean13(barcode_data):
    """Process barcode: preserve valid 13-digit EAN-13, strip and pad for UPC-A/EAN-13"""
    if not barcode_data.isdigit():
        print(f"Debug: Barcode data is not a digit: {barcode_data}")
        return None
    
    # Strip last digit
    barcode_stripped = barcode_data[:-1]
    print(f"Debug: Stripped barcode: {barcode_stripped}")
    
    # Pad stripped barcode to 13 digits
    barcode_padded = barcode_stripped.zfill(13)
    print(f"Debug: Padded barcode: {barcode_padded}")
    
    # Check if raw barcode is 13 digits and valid EAN-13
    if len(barcode_data) == 13 and int(barcode_padded[1]) > 0:
        barcode_12 = barcode_data[:-1]
        expected_check_digit = calculate_ean13_check_digit(barcode_12)
        if expected_check_digit and expected_check_digit == barcode_data[-1]:
            print(f"Debug: Raw barcode {barcode_data} has valid EAN-13 check digit, returning unchanged")
            return barcode_data
    
    # Check 2nd digit of padded barcode
    if int(barcode_padded[1]) > 0:
        # EAN-13: take last 12 digits and recalculate check digit
        barcode_12 = barcode_padded[-12:]
        check_digit = calculate_ean13_check_digit(barcode_12)
        if check_digit is not None:
            final_barcode = barcode_12 + check_digit
            print(f"Debug: EAN-13 processed - barcode_12: {barcode_12}, check_digit: {check_digit}, final_barcode: {final_barcode}")
            return final_barcode
    else:
        # UPC-A: keep padded 13-digit barcode, no check digit calculation
        print(f"Debug: UPC-A processed (2nd digit 0) - returning padded barcode: {barcode_padded}")
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
    """Detect barcode using pyzbar without preprocessing"""
    try:
        with Image.open(image_path) as img:  # Auto-close image
            barcodes = decode(img)
            if barcodes:
                barcode = barcodes[0]
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                print(f"Debug: Raw barcode detected in {image_path}: {barcode_data}")
                if barcode_data.isdigit():
                    ean13 = convert_to_ean13(barcode_data)
                    if ean13 and len(ean13) == 13:
                        print(f"Debug: Processed barcode: {ean13}")
                        return ean13, barcode_type, barcode_data
    except Exception as e:
        print(f"Error detecting barcode in {image_path}: {str(e)}")
    
    return None, None, None

def process_images(folder_path):
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    image_files = [f for f in os.listdir(folder_path) 
                   if f.lower().endswith(image_extensions)]
    
    # Sort files by creation time (earliest first)
    image_files.sort(key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
    
    # Track renamed files to avoid reprocessing
    renamed_files = set()
    
    for i, filename in enumerate(image_files):
        print(f"Debug: Processing file: {filename}")
        if filename in renamed_files:
            print(f"Debug: Skipping already renamed file: {filename}")
            continue
        
        full_path = os.path.join(folder_path, filename)
        
        barcode, barcode_type, raw_barcode = detect_barcode(full_path)
        
        if barcode and i > 0:
            prev_filename = image_files[i-1]
            prev_full_path = os.path.join(folder_path, prev_filename)
            
            # Compare base name of previous file with processed barcode
            prev_base_name = os.path.splitext(prev_filename)[0]
            print(f"Debug: Comparing prev_base_name: {prev_base_name} with processed barcode: {barcode}")
            if prev_filename not in renamed_files and prev_base_name != barcode:
                prev_ext = os.path.splitext(prev_filename)[1]
                curr_ext = os.path.splitext(filename)[1]
                new_prev_name = f"{barcode}{prev_ext}"
                new_curr_name = f"{barcode}_back{curr_ext}"
                
                try:
                    print(f"Debug: Renaming {prev_filename} to {new_prev_name}")
                    print(f"Debug: Renaming {filename} to {new_curr_name}")
                    os.rename(prev_full_path, os.path.join(folder_path, new_prev_name))
                    os.rename(full_path, os.path.join(folder_path, new_curr_name))
                    renamed_files.add(prev_filename)
                    renamed_files.add(filename)
                    
                    print(f"Renamed front image: {prev_filename} -> {new_prev_name}")
                    print(f"Renamed back image: {filename} -> {new_curr_name} "
                          f"(Barcode Type: {barcode_type}, Raw Data: {raw_barcode})")
                except OSError as e:
                    print(f"Error renaming files: {str(e)}")
            else:
                inferred_type = infer_type_from_data(raw_barcode or barcode)
                print(f"Debug: Skipping rename - prev_base_name: {prev_base_name}, barcode: {barcode}")
                print(f"Skipping rename: {prev_filename} matches or already renamed with barcode {barcode} "
                      f"(Detected Type: {barcode_type}, Inferred Type: {inferred_type})")
        elif barcode and i == 0:
            print(f"Barcode found in first image {filename} "
                  f"(Type: {barcode_type}, Raw Data: {raw_barcode}), but no previous image to rename")
        else:
            base_name = os.path.splitext(filename)[0]
            if base_name.isdigit() and len(base_name) in [12, 13]:
                inferred_type = infer_type_from_data(base_name)
                print(f"No barcode found in: {filename} after all attempts "
                      f"(Inferred Type from filename: {inferred_type})")
            else:
                print(f"No barcode found in: {filename} after all attempts")

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