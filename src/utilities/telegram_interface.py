import requests
import os
import time
from typing import Optional, Dict, Any, List, Union


class TelegramInterface:
    def __init__(self, bot_token: Optional[str] = None, channel_id: Optional[str] = None, 
                 retry_attempts: int = 3, retry_delay: int = 30):
        """
        Initialize Telegram interface with parameter-based configuration and environment variable fallbacks.
        
        Args:
            bot_token: Telegram bot token. Falls back to TELEGRAM_BOT_TOKEN environment variable.
            channel_id: Telegram channel ID. Falls back to CHANNEL_ID environment variable.
            retry_attempts: Number of retry attempts for failed requests (default: 3).
            retry_delay: Delay in seconds between retry attempts (default: 30).
        
        Raises:
            ValueError: If bot_token or channel_id are not provided and not found in environment variables.
        """
        # Use provided parameters or fall back to environment variables
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.channel_id = channel_id or os.getenv('CHANNEL_ID')
        
        # Validate required parameters
        if not self.bot_token:
            raise ValueError("Bot token must be provided as parameter or set in TELEGRAM_BOT_TOKEN environment variable")
        if not self.channel_id:
            raise ValueError("Channel ID must be provided as parameter or set in CHANNEL_ID environment variable")
        
        # Set retry configuration
        self.retry_attempts = max(1, retry_attempts)  # Ensure at least 1 attempt
        self.retry_delay = max(0, retry_delay)  # Ensure non-negative delay
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _make_request_with_retry(self, url: str, payload: Dict[str, Any], 
                                files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: The API endpoint URL
            payload: Request payload
            files: Optional files for multipart requests
            
        Returns:
            Response JSON data
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                if files:
                    response = requests.post(url, data=payload, files=files)
                else:
                    response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    # Handle HTTP errors
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    if attempt < self.retry_attempts - 1:
                        print(f"Telegram API request failed (attempt {attempt + 1}/{self.retry_attempts}): {error_msg}")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise Exception(f"Telegram API request failed after {self.retry_attempts} attempts: {error_msg}")
                        
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.retry_attempts - 1:
                    print(f"Network error (attempt {attempt + 1}/{self.retry_attempts}): {str(e)}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise Exception(f"Network error after {self.retry_attempts} attempts: {str(e)}") from e
        
        # This should not be reached, but just in case
        if last_exception:
            raise Exception(f"Request failed after {self.retry_attempts} attempts") from last_exception

    def send_message(self, text: str) -> Dict[str, Any]:
        """
        Send a text message to the configured Telegram channel.
        
        Args:
            text: Message text to send
            
        Returns:
            Telegram API response as dictionary
            
        Raises:
            Exception: If message sending fails after all retry attempts
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.channel_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        return self._make_request_with_retry(url, payload)

    def post_image_and_caption(self, image_bytes: Union[bytes, bytearray], caption: str) -> List[Dict[str, Any]]:
        """
        Post an image with caption to the configured Telegram channel.
        
        Args:
            image_bytes: Image data as bytes or bytearray, or file-like object with read() method
            caption: Caption text for the image
            
        Returns:
            List containing both photo and message API responses
            
        Raises:
            ValueError: If image_bytes is invalid
            Exception: If posting fails after all retry attempts
        """
        photo_url = f"{self.base_url}/sendPhoto"
        message_url = f"{self.base_url}/sendMessage"

        # Validate and convert image_bytes if necessary
        if not isinstance(image_bytes, (bytes, bytearray)):
            try:
                image_bytes = image_bytes.read()
            except Exception as e:
                raise ValueError("Invalid image_bytes input: must be bytes, bytearray, or file-like object with read() method") from e

        # Send photo
        payload_photo = {
            "chat_id": self.channel_id,
            "parse_mode": "Markdown",
        }
        files = {
            "photo": image_bytes
        }
        
        response_photo = self._make_request_with_retry(photo_url, payload_photo, files)
        
        # Send caption as separate message
        payload_message = {
            "chat_id": self.channel_id,
            "text": caption,
            "parse_mode": "Markdown",
        }
        
        response_message = self._make_request_with_retry(message_url, payload_message)

        return [response_message, response_photo]