import base64
import os
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

def process_uploaded_image(image_path: str) -> str:
    """Reads an image using Gemini's native vision capabilities instead of Tesseract."""
    
    # Initialize the same Gemini model you use in agent.py
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash", 
        temperature=0
    )
    
    # Convert the image to a base64 string
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
    # Send the image to Gemini and ask it to extract the text
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Extract all the text from this document exactly as it appears. Do not add any formatting or commentary, just the raw text."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]
    )
    
    try:
        response = llm.invoke([message])
        return str(response.content)
    except Exception as e:
        return f"Error processing image with Gemini: {str(e)}"