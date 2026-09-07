import pytesseract
from PIL import Image

def process_uploaded_image(image_path: str) -> str:
    try:
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text.strip() if extracted_text.strip() else "OCR Warning: No text detected in image."
    except Exception as e:
        return f"OCR Error processing image: {str(e)}"