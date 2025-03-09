import os
import ctypes
try:
    ctypes.CDLL(r"C:\Windows\System32\libzbar-64.dll")
    print("libzbar-64.dll loaded successfully")
except Exception as e:
    print(f"Failed to load libzbar-64.dll: {e}")
    raise
os.environ["PATH"] = r"C:\Windows\System32" + os.pathsep + os.environ["PATH"]
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from rembg import remove
import cv2
from pyzbar.pyzbar import decode

# Function to extract barcode from an image
def extract_barcode(image_path):
    image = Image.open(image_path)
    decoded_objects = decode(image)
    for obj in decoded_objects:
        barcode = obj.data.decode('utf-8')
        print(f"Detected barcode data: {barcode}")
        return barcode
    print("No barcode detected")
    return None

# Function to remove background and save with barcode name if available
def process_image(image_path):
    # Extract barcode from the original image first
    barcode = extract_barcode(image_path)
    
    # Open the image for background removal
    with open(image_path, 'rb') as img_file:
        input_image = img_file.read()
    
    # Process image to remove background
    output_image = remove(input_image)
    
    # Determine the output filename
    if barcode:
        # Use barcode as the filename if detected
        new_image_path = os.path.join(os.path.dirname(image_path), f"{barcode}.png")
    else:
        # Fallback to original name with '_bgr' suffix if no barcode
        new_image_path = os.path.splitext(image_path)[0] + '_bgr.png'
    
    # Save the processed image
    with open(new_image_path, 'wb') as out_file:
        out_file.write(output_image)
    
    print(f"Processed image saved as: {new_image_path}")
    return new_image_path

# Function to select images and process them
def select_files():
    # Open file dialog to select multiple image files
    file_paths = filedialog.askopenfilenames(
        title="Select Images",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")]
    )

    if file_paths:
        for file_path in file_paths:
            try:
                new_image_path = process_image(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {file_path}: {str(e)}")
        
        messagebox.showinfo("Success", "Background removal completed successfully!")
    else:
        messagebox.showwarning("No File", "No file selected. Please select image files to process.")

# Create the main window
root = tk.Tk()
root.title("Image Background Remover")

# Add a button to select images
select_button = tk.Button(root, text="Select Images", command=select_files, padx=20, pady=10)
select_button.pack(pady=20)

# Run the GUI
root.geometry("300x150")
root.mainloop()