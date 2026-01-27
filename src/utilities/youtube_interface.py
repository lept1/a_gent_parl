import os
import googleapiclient.discovery

class YouTubeInterface:
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
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=self.api_key)
        

    def get_top_videos_by_country(self, country_code, max_results: int = 10) -> dict:
        """
        Get top videos by country.
        
        Args:
            country_code: Country code (e.g., 'IT', 'US')
            
        Returns:
            dict: API response with top videos data
        """
        request = self.youtube.videos().list(
            part="contentDetails,statistics,snippet",
            chart="mostPopular",
            regionCode=country_code,
            maxResults=max_results
        )
        response = request.execute()
        return response
    
