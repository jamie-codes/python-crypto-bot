import requests
from requests.exceptions import RequestException
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Coinbase:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.coinbase.com/v2"

    def get_market_data(self, symbol):
        try:
            response = requests.get(f"{self.base_url}/prices/{symbol}/spot")
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logging.error(f"Coinbase API error: {e}")
            return None