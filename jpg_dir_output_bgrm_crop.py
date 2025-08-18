import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from rembg import remove
from io import BytesIO

# Custom function to get tight bounding box ignoring low alpha pixels
def get_tight_bbox(img, threshold=10):
    data = list(img.getdata())
    width, height = img.size
    left = width
    top = height
    right = 0
    bottom = 0
    for y in range(height):
        for x in range(width):
            a = data[y * width + x][3]
            if a >= threshold:
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)
    if left > right:
        return None
    return (left, top, right + 1, bottom + 1)

# Function to remove the background from an image, crop to content, and save resized output
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
        with open(image_path, 'rb') as img_file:
            input_image = img_file.read()
        
        # Process image to remove background
        output_image_bytes = remove(input_image)
        
        # Load the output as a PIL Image
        output_img = Image.open(BytesIO(output_image_bytes))
        
        # Ensure it's in RGBA mode for transparency
        if output_img.mode != 'RGBA':
            output_img = output_img.convert('RGBA')
        
        # Get the tight bounding box ignoring low alpha
        bbox = get_tight_bbox(output_img)
        
        if bbox:
            # Crop the image to the bounding box
            cropped_img = output_img.crop(bbox)
            
            # Resize to 300x300 for JPG output while maintaining aspect ratio
            cropped_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            jpg_bg = Image.new("RGB", (300, 300), (255, 255, 255))
            offset = ((300 - cropped_img.size[0]) // 2, (300 - cropped_img.size[1]) // 2)
            jpg_bg.paste(cropped_img, offset, mask=cropped_img.split()[3])
            
            # Save the resized image in the third-level subdirectory
            output_image_path = os.path.join(third_dir, f"{base_name}_MAIN_MAIN_THUMB.jpg")
            jpg_bg.save(output_image_path, 'JPEG')
        else:
            # If no non-transparent pixels, create an empty 300x300 white image
            jpg_bg = Image.new("RGB", (300, 300), (255, 255, 255))
            output_image_path = os.path.join(third_dir, f"{base_name}_MAIN_MAIN_THUMB.jpg")
            jpg_bg.save(output_image_path, 'JPEG')
    except Exception:
        # Skip any errors and continue processing the next file
        return

# Function to select images and destination directory, then process them
def select_files():
    # Select destination directory
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    dest_dir = filedialog.askdirectory(title="Select Destination Directory for Output")
    if not dest_dir:
        messagebox.showwarning("Warning", "No destination directory selected. Please select a directory.")
        return
    
    # Select image files
    file_paths = filedialog.askopenfilenames(
        title="Select Images", 
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")])

    if file_paths:
        for file_path in file_paths:
            process_image(file_path, dest_dir)
        
        messagebox.showinfo("Success", "Background removal and resizing completed successfully!")
    else:
        messagebox.showwarning("Warning", "No file selected. Please select image files to process.")

# Create the main window
root = tk.Tk()
root.title("Image Background Remover")

# Add a button to select images
select_button = tk.Button(root, text="Select Images and Destination", command=select_files, padx=20, pady=10)
select_button.pack(pady=20)

# Run the GUI
root.geometry("300x150")
root.mainloop()