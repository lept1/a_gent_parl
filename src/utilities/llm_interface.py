import time
import os
from google import genai
from google.genai import types

class LLMInterface:
    def __init__(self, api_key: str = None, max_retries: int = 3, retry_delay: int = 30):
        """
        Initialize LLM interface with configurable parameters.
        
        Args:
            api_key: Gemini API key. If None, uses GEMINI_API_KEY environment variable.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_delay: Base delay in seconds between retries.
        
        Raises:
            ValueError: If API key is not provided and not found in environment variables.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided or set in GEMINI_API_KEY environment variable")
        
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.gemini_client = genai.Client(api_key=self.api_key)
    
    def generate_text(self, system_instruction: str, user_query: str, model: str = "gemini-2.5-flash") -> str:
        """
        Generate text using Gemini with chat interface.
        
        Args:
            system_instruction: System instruction for the model.
            user_query: User query to process.
            model: Model name to use for generation.
            
        Returns:
            Generated text response.
            
        Raises:
            Exception: If generation fails after all retry attempts.
        """
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
        
        # Retry logic with configurable parameters
        for attempt in range(self.max_retries):
            try:
                response = chat.send_message(user_query)
                return response.text
            except Exception as e:
                print(f"Error occurred on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"Failed to generate text after {self.max_retries} attempts.")
    
    def generate_content(self, system_instruction: str, contents: str, model: str = "gemini-2.5-flash") -> str:
        """
        Generate content using Gemini with direct model interface.
        
        Args:
            system_instruction: System instruction for the model.
            contents: Content to process.
            model: Model name to use for generation.
            
        Returns:
            Generated content response.
            
        Raises:
            Exception: If generation fails after all retry attempts.
        """
        # Define the grounding tool
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        # Configure generation settings
        chat_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[grounding_tool]
        )
        
        # Retry logic with configurable parameters
        for attempt in range(self.max_retries):
            try:
                response = self.gemini_client.models.generate_content(
                    model=model,
                    config=chat_config,
                    contents=contents
                )
                return response.text
            except Exception as e:
                print(f"Error occurred on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise Exception(f"Failed to generate content after {self.max_retries} attempts.")
