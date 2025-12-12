import json
import requests

from tpex.exceptions import (
    TpexError
)
from tpex.models import ClientCredentials

class TokenManager:
    """Stores and updates data from API access."""
    def __init__(self, credentials: ClientCredentials):
        self.credentials = credentials
        self.access_token: str | None=None
        self.headers: dict | None=None
        self.wait_time: int | None=None
        # self.expires_at = 
    
    def fresh_token(self):
        """Updates access tokens."""
        body = {
            "grant_type": "client_credentials",
            "client_id": self.credentials.id,
            "client_secret": self.credentials.secret
        }

        try:
            json_response = requests.post(url=self.credentials.auth_url, data=body)
            json_response.raise_for_status()
            response = json.loads(json_response.content)
            token = response["access_token"] # potential for malformed json key error
            self.access_token = token
        except requests.exceptions.RequestException: # going to use a less vague one
            pass # this is where I can raise my custom exceptions
    
    def back_off(self):
        """Initiates backoff strategy and updates wait time."""
        if self.wait_time == 0:
            self.wait_time = 0.2
        else:
            self.wait_time *= 2