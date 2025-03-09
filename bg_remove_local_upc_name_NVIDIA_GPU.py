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
from rembg import remove, new_session
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# Create a session with CUDA provider for GPU-accelerated background removal
session = new_session(providers=["CUDAExecutionProvider"])

# Function to recover edges after background removal without altering colors
def recover_edges(img_data):
    # Decode the image data
    img_array = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
    
    # If RGBA, split channels
    if img.shape[2] == 4:
        b, g, r, a = cv2.split(img)
        rgb_img = cv2.merge((r, g, b))
    else:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        a = np.ones_like(rgb_img[:, :, 0], dtype=np.uint8) * 255
    
    # Edge detection on grayscale
    gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 30, 100)  # Lowered thresholds for more recovery
    kernel = np.ones((5, 5), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=2)  # More iterations to recover more
    
    # Use the edge mask to restore missing areas without altering colors
    # Create a mask where edges are used to fill in missing areas in the alpha channel
    if a is not None:
        # Expand the alpha channel where edges exist
        a_expanded = cv2.bitwise_or(a, edges_dilated)
    else:
        a_expanded = a
    
    # Reconstruct the image with original colors
    result = cv2.merge((b, g, r, a_expanded))
    
    # Save for debugging
    _, encoded_img = cv2.imencode('.png', result, [cv2.IMWRITE_PNG_COMPRESSION, 0])
    with open("debug_recovered.png", "wb") as debug_file:
        debug_file.write(encoded_img.tobytes())
    return encoded_img.tobytes()

# Function to remove background, recover edges, and save with barcode name
def process_image(image_path):
    barcode = extract_barcode(image_path)
    with open(image_path, 'rb') as img_file:
        input_image = img_file.read()
    # Save raw input for debugging
    with open("debug_input.png", "wb") as debug_file:
        debug_file.write(input_image)
    output_image = remove(input_image, session=session)
    # Save raw output from rembg for debugging
    with open("debug_rembg_output.png", "wb") as debug_file:
        debug_file.write(output_image)
    recovered_image = recover_edges(output_image)
    if barcode:
        new_image_path = os.path.join(os.path.dirname(image_path), f"{barcode}.png")
    else:
        new_image_path = os.path.splitext(image_path)[0] + '_bgr.png'
    with open(new_image_path, 'wb') as out_file:
        out_file.write(recovered_image)
    print(f"Processed and recovered image saved as: {new_image_path}")
    return new_image_path

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

# Function to select images and process them
def select_files():
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
        messagebox.showinfo("Success", "Background removal and edge recovery completed successfully!")
    else:
        messagebox.showwarning("No File", "No file selected. Please select image files to process.")

# Create the main window
root = tk.Tk()
root.title("Image Background Remover (GPU Accelerated)")

# Add a button to select images
select_button = tk.Button(root, text="Select Images", command=select_files, padx=20, pady=10)
select_button.pack(pady=20)

# Run the GUI
root.geometry("300x150")
root.mainloop()
