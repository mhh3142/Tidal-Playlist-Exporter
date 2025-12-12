from dataclasses import dataclass

@dataclass
class ClientCredentials:
    """Dataclass storing long term secret information."""
    id: str
    secret: str