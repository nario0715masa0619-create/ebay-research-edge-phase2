from typing import Dict, List, Optional
from .config import AuthConfig

class EbayOAuthCredentialProvider:
    def __init__(self, config: AuthConfig):
        self.config = config

    def get_client_credentials(self) -> Dict[str, str]:
        return {
            "client_id": self.config.ebay_client_id,
            "client_secret": self.config.ebay_client_secret
        }

    def get_refresh_token(self) -> Optional[str]:
        return self.config.ebay_refresh_token

    def get_redirect_uri(self) -> str:
        return self.config.ebay_redirect_uri

    def get_oauth_url(self) -> str:
        return self.config.ebay_oauth_url
