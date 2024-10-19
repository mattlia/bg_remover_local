import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
import subprocess
import os
import time

# Function to capture an image from the Canon camera using gphoto2
def capture_image():
    try:
        # Command to capture the image from the Canon camera
        capture_command = ['gphoto2', '--capture-image-and-download', '--filename', 'captured_image.jpg']
        subprocess.run(capture_command, check=True)
        print("Image captured successfully.")
        
        # Adding a delay to ensure the file is written before checking
        time.sleep(1)  # Wait 1 second to allow the file to be written
        
        # Check if the file was created before attempting to display
        if os.path.exists('captured_image.jpg'):
            # Once the image is captured, display it in the GUI
            display_image('captured_image.jpg')
        else:
            print("Capture failed: Image file not found.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error capturing image: {e}")

# Function to display the captured image in the GUI
def display_image(image_path):
    try:
        # Open the image using Pillow
        img = Image.open(image_path)
        
        # Resize the image to fit into the GUI window
        img = img.resize((400, 300), Image.ANTIALIAS)
        
        # Convert the image to a format that Tkinter can use
        img_tk = ImageTk.PhotoImage(img)
        
        # Update the image label with the new image
        image_label.config(image=img_tk)
        image_label.image = img_tk  # Keep a reference to avoid garbage collection

    except FileNotFoundError:
        print(f"Error: {image_path} not found.")
    except Exception as e:
        print(f"An error occurred while displaying the image: {e}")

# Function to create the main window
def create_gui():
    global image_label

    # Create the main application window
    root = tk.Tk()
    root.title("Canon Camera Image Capture")

    # Create a button to capture the image
    capture_button = tk.Button(root, text="Capture Image", command=capture_image, height=2, width=20)
    capture_button.pack(pady=20)

    # Label to display the captured image
    image_label = Label(root)
    image_label.pack(pady=10)

    # Run the main event loop
    root.mainloop()

# Start the GUI application
if __name__ == "__main__":
    create_gui()
