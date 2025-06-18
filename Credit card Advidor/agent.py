import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables. Please check your .env file.")
    exit()

# Configure the generative AI model
genai.configure(api_key=GEMINI_API_KEY)
def list_available_models():
    """
    Lists all available Gemini models and their supported methods.
    """
    print("\n--- Available Gemini Models ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}, Supported Methods: {m.supported_generation_methods}")
    print("-------------------------------\n")
def get_llm_response(prompt):
    """
    Sends a prompt to the Google Gemini LLM and returns the response.
    """
    try:
        # You can try 'gemini-pro' or 'gemini-1.5-pro-latest' if you have access and want to try it
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred with Gemini: {e}")
        return "Error: Could not get response from LLM."

# --- Test the LLM interaction ---
if __name__ == "__main__":
    list_available_models()
    print("Testing Gemini LLM response...")
    test_prompt = "What are the benefits of a credit card?"
    llm_answer = get_llm_response(test_prompt)
    print(f"\nYour Prompt: {test_prompt}")
    print(f"LLM Answer: {llm_answer}")

    print("\nTesting another prompt...")
    test_prompt_2 = "Summarize the key features of a good travel credit card."
    llm_answer_2 = get_llm_response(test_prompt_2)
    print(f"\nYour Prompt: {test_prompt_2}")
    print(f"LLM Answer: {llm_answer_2}")