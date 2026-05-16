from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class CliExecutionContext:
    command_path: str
    output_format: str = "table" # table, json, text
    verbose: bool = False
    dry_run: bool = True
    force: bool = False
    force_recheck: bool = False
    limit: Optional[int] = None
    confirm: bool = False
    invoked_at: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None

@dataclass
class CliCommandResult:
    command_path: str
    status: str = "success" # success, error, warning, confirmation_required
    message: Optional[str] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    records: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    exit_code: int = 0
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CliRecordView:
    record_type: str
    primary_id: str
    fields: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
