"""
Audit logger for execution tracking.
Logs SKU, images used, execution mode, and results.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from src.listing_execution.models.execution_payload import ExecutionPayload
import logging
import json

logger = logging.getLogger(__name__)

class ExecutionAuditLogger:
    """
    Logs execution details for audit trail.
    Tracks: SKU, title, images, mode (dry-run/live), result, error.
    """
    
    def __init__(self, log_file: str = "logs/execution_audit.jsonl"):
        """Initialize with log file path."""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_payload_validation(
        self,
        sku: str,
        is_valid: bool,
        image_count: int,
        image_paths: Optional[List[Path]] = None,
        errors: Optional[List[str]] = None
    ) -> None:
        """Log payload validation result."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "payload_validation",
            "sku": sku,
            "is_valid": is_valid,
            "image_count": image_count,
            "image_paths": [str(p) for p in (image_paths or [])],
            "errors": errors or []
        }
        self._write_record(record)
    
    def log_execution_start(
        self,
        payload: ExecutionPayload
    ) -> None:
        """Log execution start."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "execution_start",
            "sku": payload.sku,
            "listing_id": payload.listing_id,
            "attempt_id": payload.attempt_id,
            "title": payload.title,
            "mode": "dry_run" if payload.dry_run else "live",
            "image_count": len(payload.image_urls),
            "image_urls": payload.image_urls,
            "price": payload.price,
            "condition": payload.condition
        }
        self._write_record(record)
    
    def log_execution_success(
        self,
        sku: str,
        listing_id: str,
        attempt_id: str,
        mode: str,
        image_count: int,
        ebay_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log execution success."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "execution_success",
            "sku": sku,
            "listing_id": listing_id,
            "attempt_id": attempt_id,
            "mode": mode,
            "image_count": image_count,
            "ebay_response_summary": ebay_response or {}
        }
        self._write_record(record)
    
    def log_execution_failure(
        self,
        sku: str,
        listing_id: str,
        attempt_id: str,
        mode: str,
        image_count: int,
        error_message: str,
        error_code: Optional[str] = None
    ) -> None:
        """Log execution failure."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "execution_failure",
            "sku": sku,
            "listing_id": listing_id,
            "attempt_id": attempt_id,
            "mode": mode,
            "image_count": image_count,
            "error_code": error_code,
            "error_message": error_message
        }
        self._write_record(record)
    
    def log_execution_skip(
        self,
        sku: str,
        reason: str
    ) -> None:
        """Log execution skip."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "execution_skip",
            "sku": sku,
            "reason": reason
        }
        self._write_record(record)
    
    def _write_record(self, record: Dict[str, Any]) -> None:
        """Write JSONL record."""
        try:
            with open(self.log_file, mode='a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
