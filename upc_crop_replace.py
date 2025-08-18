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
        
        # Save the image overwriting the original file as JPG
        white_bg.save(image_path, 'JPEG')
    else:
        # If no non-transparent pixels, create an empty white image
        white_bg = Image.new("RGB", (1, 1), (255, 255, 255))
        white_bg.save(image_path, 'JPEG')

# Function to select images and process them
def select_files():
    # Open file dialog to select multiple image files
    file_paths = filedialog.askopenfilenames(
        title="Select Images", 
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")])

    if file_paths:
        for file_path in file_paths:
            try:
                process_image(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {file_path}: {str(e)}")
        
        messagebox.showinfo("Success", "Background removal completed successfully!")
    else:
        messagebox.showwarning("Warning", "No file selected. Please select image files to process.")

# Create the main window
root = tk.Tk()
root.title("Image Background Remover")

# Add a button to select images
select_button = tk.Button(root, text="Select Images", command=select_files, padx=20, pady=10)
select_button.pack(pady=20)

# Run the GUI
root.geometry("300x150")
root.mainloop()