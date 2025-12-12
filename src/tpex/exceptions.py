class TpexError(Exception):
    """Base exception for tpex."""
    pass

class TidalAuthError(TpexError):
    """Raised on 401 HTTP errors."""
    def __init__(self, message: str, wait_time: int, expired: bool):
        self.message = message
        self.wait_time = wait_time
        self.expired = expired
        super().__init__(f"TidalHTTPError, 401 BAD_TOKENS: {message}")

class TidalRateLimitError(TpexError):
    """Raised on 429 HTTP errors."""
    def __init__(self, wait_time: int, expired: bool):
        super().__init__(f"Rate limited by Tidal 429")

class TidalHTTPError(TpexError):
    """Raised on bad API responses, catches non 2xx status codes not dealt with by auth and rate limit error."""
    def __init__(self, status_code: int, message: str, response=None):
        self.status_code = status_code
        self.message = message
        self.response = response
        super().__init__(f"TidalHTTPError {status_code}: {message}")

class TidalResponseFormatError(TpexError):
    """Raised on json with missing keys or an api response that doesn't look how I'd expect."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Unexpected JSON response: {status_code}, {message}")

class TidalJSONDecodeError(TpexError):
    """Raised when json doesn't convert to python object."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"JSONDecodeError, {status_code}: {message}")