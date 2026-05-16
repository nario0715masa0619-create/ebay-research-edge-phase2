from typing import List, Dict, Any
from tabulate import tabulate

class CliTableRenderer:
    def render(self, data: List[Dict[str, Any]], headers: List[str] = None) -> str:
        if not data:
            return "No data found."
        
        if not headers:
            headers = "keys"
        
        return tabulate(data, headers=headers, tablefmt="simple")
