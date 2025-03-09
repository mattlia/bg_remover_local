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

# Function to correct image rotation using GPU
def correct_rotation_gpu(img):
    gpu_img = cv2.cuda_GpuMat()
    gpu_img.upload(img)
    # Use Hough Transform to detect lines and estimate rotation
    gpu_lines = cv2.cuda.createHoughSegmentDetector()
    lines = gpu_lines.detect(gpu_img)
    if lines is not None:
        lines = lines.download()
        angle = 0
        for line in lines[0]:
            x1, y1, x2, y2 = line
            angle += np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        angle /= len(lines[0]) if len(lines[0]) > 0 else 1
        # Rotate image on GPU
        if abs(angle) > 1:  # Only rotate if significant
            center = (gpu_img.cols // 2, gpu_img.rows // 2)
            rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            gpu_rotated = cv2.cuda.warpAffine(gpu_img, rot_matrix, (gpu_img.cols, gpu_img.rows))
            return gpu_rotated.download()
    return img

# Function to extract barcode with GPU-enhanced accuracy
def extract_barcode(image_path):
    # Load image with OpenCV
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    try:
        # Upload to GPU
        gpu_img = cv2.cuda_GpuMat()
        gpu_img.upload(img)
        
        # GPU pre-processing: Enhance contrast and correct rotation
        gpu_clahe = cv2.cuda.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gpu_enhanced = gpu_clahe.apply(gpu_img)
        enhanced_img = correct_rotation_gpu(gpu_enhanced.download())
        
        # GPU thresholding
        gpu_thresh = cv2.cuda.createAdaptiveThreshold(11, 2, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 255)
        gpu_result = gpu_thresh.apply(gpu_enhanced)
        thresh = gpu_result.download()
    except AttributeError:
        # Fallback to CPU if cv2.cuda isn’t available
        print("CUDA not available, falling back to CPU pre-processing")
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_img = clahe.apply(img)
        thresh = cv2.adaptiveThreshold(enhanced_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Convert to PIL Image for pyzbar
    pil_img = Image.fromarray(thresh)
    
    # Decode barcode with pyzbar (CPU)
    decoded_objects = decode(pil_img)
    for obj in decoded_objects:
        barcode = obj.data.decode('utf-8')
        print(f"Detected barcode data: {barcode}")
        return barcode
    
    # Fallback: Try original image if enhanced fails
    original_pil = Image.open(image_path)
    decoded_objects = decode(original_pil)
    for obj in decoded_objects:
        barcode = obj.data.decode('utf-8')
        print(f"Detected barcode data (original): {barcode}")
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
    
    # Process image to remove background using GPU
    output_image = remove(input_image, session=session)
    
    # Determine the output filename
    if barcode:
        new_image_path = os.path.join(os.path.dirname(image_path), f"{barcode}.png")
    else:
        new_image_path = os.path.splitext(image_path)[0] + '_bgr.png'
    
    # Save the processed image
    with open(new_image_path, 'wb') as out_file:
        out_file.write(output_image)
    
    print(f"Processed image saved as: {new_image_path}")
    return new_image_path

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
        
        messagebox.showinfo("Success", "Background removal completed successfully!")
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