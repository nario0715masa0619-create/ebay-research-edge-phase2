from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.db.models import ReportArtifactModel

class ReportArtifactRepositoryDB:
    def __init__(self, session: Session):
        self.session = session

    def create_artifact(self, artifact: ReportArtifactModel) -> str:
        self.session.add(artifact)
        self.session.commit()
        self.session.refresh(artifact)
        return artifact.report_id

    def get_artifact_by_id(self, report_id: str) -> Optional[ReportArtifactModel]:
        return self.session.get(ReportArtifactModel, report_id)

    def list_recent_artifacts(self, limit: int = 20) -> List[ReportArtifactModel]:
        stmt = select(ReportArtifactModel).order_by(ReportArtifactModel.generated_at.desc()).limit(limit)
        return list(self.session.scalars(stmt))

    def list_by_report_type(self, report_type: str) -> List[ReportArtifactModel]:
        stmt = select(ReportArtifactModel).where(ReportArtifactModel.report_type == report_type).order_by(ReportArtifactModel.generated_at.desc())
        return list(self.session.scalars(stmt))

    def list_by_seller(self, seller_id: str) -> List[ReportArtifactModel]:
        stmt = select(ReportArtifactModel).where(ReportArtifactModel.seller_account_id == seller_id).order_by(ReportArtifactModel.generated_at.desc())
        return list(self.session.scalars(stmt))

    def update_artifact(self, report_id: str, updates: dict) -> bool:
        artifact = self.get_artifact_by_id(report_id)
        if not artifact:
            return False
        for key, value in updates.items():
            setattr(artifact, key, value)
        self.session.commit()
        return True

    def soft_delete(self, report_id: str) -> bool:
        return self.update_artifact(report_id, {"is_deleted": True})

    def get_active_artifacts(self, limit: int = 20) -> List[ReportArtifactModel]:
        stmt = select(ReportArtifactModel).where(ReportArtifactModel.is_deleted == False).order_by(ReportArtifactModel.generated_at.desc()).limit(limit)
        return list(self.session.scalars(stmt))
