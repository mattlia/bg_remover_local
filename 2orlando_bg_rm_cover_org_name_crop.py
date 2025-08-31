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

# Function to remove the background from an image and crop to content
def process_image(image_path):
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
            
            # Create a white background for JPG
            white_bg = Image.new("RGB", cropped_img.size, (255, 255, 255))
            white_bg.paste(cropped_img, mask=cropped_img.split()[3])  # Use alpha as mask
            
            # Save the image with the same name, overwriting the original, as JPG
            output_image_path = os.path.splitext(image_path)[0] + '.jpg'
            white_bg.save(output_image_path, 'JPEG')
        else:
            # If no non-transparent pixels, create an empty white image
            white_bg = Image.new("RGB", (1, 1), (255, 255, 255))
            output_image_path = os.path.splitext(image_path)[0] + '.jpg'
            white_bg.save(output_image_path, 'JPEG')
    except Exception as e:
        raise Exception(f"Failed to process {image_path}: {str(e)}")

# Function to select source directory and process images
def select_files():
    # Select source directory
    root = tk.Tk()
    root.withdraw()  # Hide the root window
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
                try:
                    process_image(file_path)
                    processed_count += 1
                except Exception as e:
                    messagebox.showerror("Error", str(e))
    
    if processed_count > 0:
        messagebox.showinfo("Success", f"Processed {processed_count} images successfully!")
    else:
        messagebox.showwarning("Warning", "No valid image files found in the selected directory or its subdirectories.")

# Create the main window
root = tk.Tk()
root.title("Image Background Remover")

# Add a button to select directory
select_button = tk.Button(root, text="Select Source Directory", command=select_files, padx=20, pady=10)
select_button.pack(pady=20)

# Run the GUI
root.geometry("300x150")
root.mainloop()