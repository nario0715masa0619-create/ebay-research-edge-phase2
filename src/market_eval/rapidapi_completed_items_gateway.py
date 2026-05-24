import urllib.parse
from typing import List, Dict, Any
import requests
from requests.exceptions import RequestException

from .market_search_gateway import MarketSearchGateway, GatewayResponse
from .models import MarketSearchRequest
from .config import MarketEvalSettings

class RapidApiCompletedItemsGateway(MarketSearchGateway):
    """
    Live gateway that calls the RapidAPI 'eBay Average Selling Price' (ecommet) findCompletedItems endpoint.
    """
    def __init__(self, settings: MarketEvalSettings):
        self.settings = settings
        self.api_key = self.settings.rapidapi_key
        self.api_host = self.settings.rapidapi_host
        
        if not self.api_key or not self.api_host:
            raise ValueError("RAPIDAPI_KEY and RAPIDAPI_HOST must be provided for live gateway")
            
    def search_completed_items(self, request: MarketSearchRequest) -> GatewayResponse:
        url = f"https://{self.api_host}/findCompletedItems"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host,
        }
        
        # Build query parameters
        params = {
            "keywords": request.query,
            "categoryId": request.category_id or "",
            "limit": str(request.limit),
            "sortOrder": request.sort,
            "siteId": "0" if request.marketplace_id == "EBAY_US" else "0", # simplified mapping
        }
        
        # In RapidAPI ecommet, itemFilter is often passed as indexed parameters or JSON depending on the exact schema.
        # Following the generic findCompletedItems pattern:
        filter_idx = 0
        for k, v in request.filters.items():
            params[f"itemFilter({filter_idx}).name"] = k
            params[f"itemFilter({filter_idx}).value"] = v
            filter_idx += 1

        unsafe_reasons = []
        raw_items = []
        
        try:
            # We use timeout from settings to avoid hanging
            response = requests.get(url, headers=headers, params=params, timeout=self.settings.provider_timeout_seconds)
            
            if response.status_code == 429:
                unsafe_reasons.append("provider_rate_limit: RapidAPI rate limit exceeded")
            elif response.status_code >= 400:
                unsafe_reasons.append(f"provider_error: HTTP {response.status_code} - {response.text[:100]}")
            else:
                data = response.json()
                # Assuming standard eBay finding API shape inside RapidAPI wrapper
                # e.g., data["findCompletedItemsResponse"][0]["searchResult"][0]["item"]
                # We do a safe extraction:
                resp = data.get("findCompletedItemsResponse", [{}])[0]
                ack = resp.get("ack", [""])[0]
                
                if ack.lower() in ("success", "warning"):
                    search_result = resp.get("searchResult", [{}])[0]
                    items = search_result.get("item", [])
                    if isinstance(items, list):
                        raw_items = items
                    else:
                        unsafe_reasons.append("parse_failure: 'item' is not a list in response")
                else:
                    err_msg = str(resp.get("errorMessage", ["Unknown error"]))
                    unsafe_reasons.append(f"provider_error: ack={ack}, msg={err_msg[:100]}")
                    
        except requests.exceptions.Timeout:
            unsafe_reasons.append(f"provider_timeout: Request exceeded {self.settings.provider_timeout_seconds}s")
        except RequestException as e:
            unsafe_reasons.append(f"provider_error: Request failed - {str(e)[:100]}")
        except ValueError:
            unsafe_reasons.append("parse_failure: Invalid JSON response")
            
        return GatewayResponse(
            raw_items=raw_items,
            provider_name="rapidapi_completed",
            unsafe_reasons=unsafe_reasons
        )
