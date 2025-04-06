import google.generativeai as genai
from PIL import Image


def analyze_image_with_gemini(image_path, api_key):
    """
    Analyze an image using Google's Gemini model with custom prompts
    """
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Open and prepare the image
    image = Image.open(image_path)

    with open("prompt.txt", "r") as f:
        prompt = f.read()

    # Generate content with both image and prompt
    response = model.generate_content(
        [
            prompt,    # Your text prompt
            image      # Your image
        ]
    )
    
    return response.text