import uuid
from typing import List, Optional, Dict
from src.listing_execution.models.report_artifact import ReportArtifact

class ReportArtifactRepository:
    """
    In-memory mock repository for ReportArtifacts.
    Database persistence (report_artifacts table) will be implemented in Wave 6.
    """
    def __init__(self):
        self._storage: Dict[str, ReportArtifact] = {}

    def create_artifact(self, artifact: ReportArtifact) -> str:
        if not artifact.metadata.report_id:
            artifact.metadata.report_id = str(uuid.uuid4())
        self._storage[artifact.metadata.report_id] = artifact
        return artifact.metadata.report_id

    def get_artifact_by_id(self, artifact_id: str) -> Optional[ReportArtifact]:
        return self._storage.get(artifact_id)

    def list_recent_artifacts(self, limit: int = 20) -> List[ReportArtifact]:
        sorted_artifacts = sorted(
            self._storage.values(),
            key=lambda a: a.metadata.generated_at,
            reverse=True
        )
        return sorted_artifacts[:limit]

    def list_by_report_type(self, report_type: str) -> List[ReportArtifact]:
        filtered = [a for a in self._storage.values() if a.metadata.report_type == report_type]
        sorted_artifacts = sorted(
            filtered,
            key=lambda a: a.metadata.generated_at,
            reverse=True
        )
        return sorted_artifacts

    def list_by_seller(self, seller_id: str) -> List[ReportArtifact]:
        filtered = [
            a for a in self._storage.values() 
            if a.metadata.applied_filters.get("seller_account_id") == seller_id
        ]
        sorted_artifacts = sorted(
            filtered,
            key=lambda a: a.metadata.generated_at,
            reverse=True
        )
        return sorted_artifacts
