import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
import os

class LLMInterface:
    def __init__(self, env_path='.env'):
        load_dotenv(env_path)
        
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        self.gemini_client = genai.Client(api_key=self.GEMINI_API_KEY)
    
    def generate_text(self, system_instruction, user_query, model="gemini-2.5-flash"):
        # Define the grounding tool
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        # Configure generation settings
        chat_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[grounding_tool]
        )
        chat = self.gemini_client.chats.create(
            model=model,
            config=chat_config
        )
        #try to send the message and retry 3 times if it fails with a delay of 30 seconds
        for i in range(3):
            try:
                response = chat.send_message(user_query)
                return response.text
            except Exception as e:
                print(f"Error occurred: {e}")
                time.sleep(30)
        return f"An error occurred while generating text. {e}"
