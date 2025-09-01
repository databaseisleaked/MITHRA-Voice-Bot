import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: API key not found in .env file.")
    exit()

genai.configure(api_key=api_key)

model = genai.GenerativeModel(model_name="gemini-2.0-flash")

try:
    response = model.generate_content("What is the capital of France?")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")