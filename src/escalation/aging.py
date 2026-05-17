from typing import Optional

def calculate_aging_bucket(seconds: int) -> str:
    """
    Categorizes the age of an escalation state into standardized buckets.
    """
    if seconds < 15 * 60:
        return "0_15m"
    elif seconds < 60 * 60:
        return "15m_1h"
    elif seconds < 4 * 60 * 60:
        return "1h_4h"
    elif seconds < 24 * 60 * 60:
        return "4h_24h"
    else:
        return "24h_plus"
