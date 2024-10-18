
import os
import ctypes
import cv2

# Set DYLD_LIBRARY_PATH to include the Homebrew library path
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib'

# Load the ZBar library using its full path
try:
    zbar_lib = ctypes.CDLL('/opt/homebrew/lib/libzbar.dylib')
    print("ZBar library loaded successfully!")
except OSError as e:
    raise ImportError(f"Unable to load ZBar library: {e}")

from pyzbar.pyzbar import decode

# Set the resolution for the captured images
CAPTURE_WIDTH = 1920  # Width of the image
CAPTURE_HEIGHT = 1080  # Height of the image

# Folder to save images
SAVE_FOLDER = "product_images"

# Function to initialize the webcam with higher resolution
def setup_camera():
    cap = cv2.VideoCapture(1)  # Change the index if multiple cameras are connected
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
    return cap

# Function to display text on the video frame
def display_text_on_frame(frame, text):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    font_color = (0, 255, 0)  # Green
    font_thickness = 3
    text_position = (50, 100)  # Starting position for the text
    cv2.putText(frame, text, text_position, font, font_scale, font_color, font_thickness, cv2.LINE_AA)

# Function to scan the barcode
def scan_barcode():
    cap = setup_camera()
    while True:
        ret, frame = cap.read()
        barcodes = decode(frame)
        if barcodes:
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8')
                display_text_on_frame(frame, f"Barcode found: {barcode_data}")
                cap.release()
                cv2.destroyAllWindows()
                return barcode_data
        else:
            display_text_on_frame(frame, "Scanning for barcode... Press 'q' to quit.")
        
        cv2.imshow('Barcode Scanner (Press "q" to quit)', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Function to capture and save an image (front or back)
def capture_image(barcode, position):
    cap = setup_camera()
    while True:
        ret, frame = cap.read()
        display_text_on_frame(frame, f"Position the product {position}. Press 'c' to capture, 'q' to quit.")
        cv2.imshow(f'Capturing {position} image for barcode {barcode}', frame)
        
        # Press 'c' to capture the image
        if cv2.waitKey(1) & 0xFF == ord('c'):
            filepath = os.path.join(SAVE_FOLDER, f"{barcode}_{position}.jpg")
            cv2.imwrite(filepath, frame)
            display_text_on_frame(frame, f"{position.capitalize()} image saved: {filepath}")
            break
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Function to check if images for a barcode already exist
def check_existing_images(barcode):
    front_image = os.path.join(SAVE_FOLDER, f"{barcode}_front.jpg")
    back_image = os.path.join(SAVE_FOLDER, f"{barcode}_back.jpg")

    # Check if both images (front and back) exist
    if os.path.exists(front_image) and os.path.exists(back_image):
        return True
    return False

# Function to prompt the operator whether to retake images
def prompt_retake():
    while True:
        response = input("Images for this barcode already exist. Do you want to retake them? (Y/N): ").strip().lower()
        if response == 'y':
            return True
        elif response == 'n':
            return False
        else:
            print("Invalid input. Please enter 'Y' for yes or 'N' for no.")

# Create the save folder if it doesn't exist
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

# Main workflow
def main():
    display_text_on_frame(None, "Step 1: Scan the product barcode.")
    barcode = scan_barcode()
    
    if barcode:
        # Check if images for the barcode already exist
        if check_existing_images(barcode):
            # Ask the operator if they want to retake the images
            if not prompt_retake():
                display_text_on_frame(None, f"Skipping capture for product {barcode}.")
                return
        
        # Proceed to capture images if not skipping
        display_text_on_frame(None, f"Step 2: Capture front image for product {barcode}.")
        capture_image(barcode, "front")
        
        display_text_on_frame(None, f"Step 3: Capture back image for product {barcode}.")
        capture_image(barcode, "back")
    else:
        display_text_on_frame(None, "No barcode detected. Please try again.")

if __name__ == "__main__":
    main()
