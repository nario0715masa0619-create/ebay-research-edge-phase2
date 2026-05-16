import json
from typing import Any, Dict, List
from .models import CliCommandResult
from .table_renderer import CliTableRenderer

class CliOutputFormatter:
    def __init__(self):
        self.table_renderer = CliTableRenderer()

    def format(self, result: CliCommandResult, fmt: str = "table") -> str:
        if fmt == "json":
            return json.dumps({
                "status": result.status,
                "message": result.message,
                "summary": result.summary,
                "records": result.records,
                "errors": result.errors,
                "meta": result.meta
            }, indent=2, default=str)
        
        elif fmt == "text":
            lines = []
            if result.message: lines.append(f"MESSAGE: {result.message}")
            if result.summary:
                lines.append("SUMMARY:")
                for k, v in result.summary.items():
                    lines.append(f"  {k}: {v}")
            if result.errors:
                lines.append("ERRORS:")
                for e in result.errors:
                    lines.append(f"  - {e}")
            return "\n".join(lines)
        
        else: # table
            lines = []
            if result.message: lines.append(result.message)
            if result.summary:
                lines.append("\nSummary:")
                for k, v in result.summary.items():
                    lines.append(f"  {k}: {v}")
            
            if result.records:
                lines.append("\n" + self.table_renderer.render(result.records))
                
            if result.errors:
                lines.append("\nErrors:")
                for e in result.errors:
                    lines.append(f"  !! {e}")
                    
            return "\n".join(lines)
