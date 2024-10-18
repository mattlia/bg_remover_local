import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from rembg import remove

# Function to remove the background from an image
def process_image(image_path):
    # Open the image
    with open(image_path, 'rb') as img_file:
        input_image = img_file.read()
    
    # Process image to remove background
    output_image = remove(input_image)
    
    # Save the new image with "_bgr" appended to the name
    new_image_path = os.path.splitext(image_path)[0] + '_bgr.png'
    with open(new_image_path, 'wb') as out_file:
        out_file.write(output_image)

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
