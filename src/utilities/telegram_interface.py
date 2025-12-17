import requests
import os


class TelegramInterface:
    def __init__(self):
        
        try:
            self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        except KeyError:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables.")
        
        try:
            self.CHANNEL_ID = os.getenv("CHANNEL_ID")
        except KeyError:
            raise ValueError("CHANNEL_ID not found in environment variables.")
        
        self.base_url = f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}"

    def send_message(self, text):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.CHANNEL_ID,
            "text": text,
            "parse_mode": "Markdown",
        }
        response = requests.post(url, json=payload)
        return response.json()

    def post_image_and_caption(self, image_bytes, caption):
        
        photo_url = f"{self.base_url}/sendPhoto"
        message_url = f"{self.base_url}/sendMessage"

        payload_photo = {
            "chat_id": self.CHANNEL_ID,
            "parse_mode": "Markdown",
        }

        #verify image_bytes is a BytesIO object try converting to bytes
        if not isinstance(image_bytes, (bytes, bytearray)):
            try:
                image_bytes = image_bytes.read()
            except Exception as e:
                raise ValueError("Invalid image_bytes input") from e

        files = {
            "photo": image_bytes
        }
        payload_message = {
            "chat_id": self.CHANNEL_ID,
            "text": caption,
            "parse_mode": "Markdown",
        }
        
        response_photo = requests.post(photo_url, data=payload_photo, files=files)
        if response_photo.status_code != 200:
            raise Exception(f"Failed to send photo: {response_photo.text}")
        
        response_message = requests.post(message_url, json=payload_message)
        if response_message.status_code != 200:
            raise Exception(f"Failed to send message: {response_message.text}")

        return [response_message.json(), response_photo.json()]