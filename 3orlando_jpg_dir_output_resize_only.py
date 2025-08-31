import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# Function to process an image and save resized output
def process_image(image_path, dest_dir):
    # Get the base filename (without extension)
    base_name = os.path.basename(os.path.splitext(image_path)[0])
    
    # Skip if filename is not numeric or has fewer than 13 digits
    if not (base_name.isdigit() and len(base_name) >= 13):
        return
    
    # Extract subdirectory names based on filename digits
    first_level = base_name[:3]  # First 3 digits
    second_level = base_name[3:8]  # 4th to 8th digits
    third_level = base_name[-5:]  # Last 5 digits
    
    # Create three-level subdirectory structure in destination directory
    first_dir = os.path.join(dest_dir, first_level)
    second_dir = os.path.join(first_dir, second_level)
    third_dir = os.path.join(second_dir, third_level)
    
    # Check if subdirectories exist before creating
    if not os.path.exists(first_dir):
        os.makedirs(first_dir, exist_ok=True)
    if not os.path.exists(second_dir):
        os.makedirs(second_dir, exist_ok=True)
    if not os.path.exists(third_dir):
        os.makedirs(third_dir, exist_ok=True)
    
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Ensure it's in RGBA mode for transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Resize to 300x300 for JPG output while maintaining aspect ratio
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            jpg_bg = Image.new("RGB", (300, 300), (255, 255, 255))
            offset = ((300 - img.size[0]) // 2, (300 - img.size[1]) // 2)
            jpg_bg.paste(img, offset, mask=img.split()[3])
            
            # Save the resized image in the third-level subdirectory
            output_image_path = os.path.join(third_dir, f"{base_name}_MAIN_MAIN_THUMB.jpg")
            jpg_bg.save(output_image_path, 'JPEG')
    except Exception:
        # Skip any errors and continue processing the next file
        return

# Function to select source and destination directories, then process images
def select_files():
    # Select destination directory
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    dest_dir = filedialog.askdirectory(title="Select Destination Directory for Output")
    if not dest_dir:
        messagebox.showwarning("Warning", "No destination directory selected. Please select a directory.")
        return
    
    # Select source directory
    src_dir = filedialog.askdirectory(title="Select Source Directory with Images")
    if not src_dir:
        messagebox.showwarning("Warning", "No source directory selected. Please select a directory.")
        return
    
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    processed_count = 0
    
    # Walk through source directory and subdirectories
    for root_dir, _, files in os.walk(src_dir):
        for file_name in files:
            if file_name.lower().endswith(image_extensions):
                file_path = os.path.join(root_dir, file_name)
                process_image(file_path, dest_dir)
                processed_count += 1
    
    if processed_count > 0:
        messagebox.showinfo("Success", f"Processed {processed_count} images successfully!")
    else:
        messagebox.showwarning("Warning", "No valid image files found in the selected directory or its subdirectories.")

# Create the main window
root = tk.Tk()
root.title("Image Processor")

# Add a button to select directories
select_button = tk.Button(root, text="Select Source and Destination Directories", command=select_files, padx=20, pady=10)
select_button.pack(pady=20)

# Run the GUI
root.geometry("300x150")
root.mainloop()