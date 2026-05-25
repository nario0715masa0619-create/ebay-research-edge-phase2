from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from src.listing_execution.models.report_metadata import ReportMetadata

@dataclass
class ReportArtifact:
    metadata: ReportMetadata
    artifact_path: Optional[str] = None
    blob_ref: Optional[str] = None
    generated_by: str = ""
    trigger_source: str = ""

@dataclass
class ExportRow:
    """汎用行データモデル（CSV/JSON 出力向け）"""
    row_data: Dict[str, Any] = field(default_factory=dict)
