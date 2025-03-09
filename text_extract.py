import os
from tkinter import filedialog, Tk, Label, Button
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw
from collections import Counter

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Function to extract text and draw boxes on a single image
def process_image_with_boxes(image_path):
    # Perform OCR
    result = ocr.ocr(image_path, cls=True)
    extracted_text = ' '.join([line[1][0] for line in result[0]])  # Extract text
    
    # Open image and create drawing object
    image = Image.open(image_path).convert('RGB')
    draw = ImageDraw.Draw(image)
    
    # Draw blue boxes around detected text
    for line in result[0]:
        # Get bounding box coordinates
        box = line[0]
        # Convert coordinates to format: (left, top, right, bottom)
        left = min(box[0][0], box[3][0])
        top = min(box[0][1], box[1][1])
        right = max(box[1][0], box[2][0])
        bottom = max(box[2][1], box[3][1])
        
        # Draw blue rectangle (outline only)
        draw.rectangle([left, top, right, bottom], outline='blue', width=2)
    
    # Save the modified image
    output_path = os.path.join(
        os.path.dirname(image_path),
        f"boxed_{os.path.basename(image_path)}"
    )
    image.save(output_path)
    return extracted_text, output_path

# Function to process selected images and extract text
def extract_text_from_images(image_paths):
    text_data = []
    for image_path in image_paths:
        extracted_text, output_path = process_image_with_boxes(image_path)
        print(f"Extracted text from {os.path.basename(image_path)}:\n{extracted_text}")
        print(f"Saved image with boxes to: {output_path}\n")
        text_data.append(extracted_text)
    return text_data

# Function to infer the product name from aggregated text
def infer_product_name_from_text(text_data):
    combined_text = ' '.join(text_data)
    # Define stopwords to remove irrelevant words
    stopwords = ['ingredients', 'nutrition', 'facts', 'serving', 'calories', 'total', 'fat', 'carbs', 'sugars']
    
    # Split the text and filter out stopwords
    words = combined_text.split()
    filtered_words = [word for word in words if word.lower() not in stopwords]
    
    # Count word frequency and find the most common words
    word_counter = Counter(filtered_words)
    most_common_words = word_counter.most_common(5)  # Get the 5 most common words
    return ' '.join([word for word, count in most_common_words])

# Function to select multiple images and process them
def process_images():
    file_paths = filedialog.askopenfilenames(
        title="Select Images", 
        filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
    )
    
    if file_paths:
        # Extract text from the selected images
        extracted_texts = extract_text_from_images(file_paths)
        
        if extracted_texts:
            # Infer the product name based on the extracted text
            product_name = infer_product_name_from_text(extracted_texts)
            print(f"Possible Product Name: {product_name}")
            result_label.config(text=f"Possible Product Name: {product_name}")
        else:
            result_label.config(text="No text data extracted from the images.")
    else:
        result_label.config(text="No images selected.")

# Initialize the Tkinter GUI
root = Tk()
root.title("Product Name Inference")
root.geometry("400x200")

# Create and display labels and buttons
label = Label(root, text="Select Images to Analyze Product", font=("Helvetica", 14))
label.pack(pady=20)

button = Button(root, text="Select Images", command=process_images, font=("Helvetica", 12))
button.pack(pady=10)

result_label = Label(root, text="", font=("Helvetica", 12))
result_label.pack(pady=10)

# Start the Tkinter GUI event loop
root.mainloop()