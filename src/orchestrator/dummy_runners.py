from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class DummyBatchResult:
    run_id: str = "dummy"
    processed_count: int = 0
    success_count: int = 0
    skipped_count: int = 0
    success_flag: bool = True

class SourceCollector:
    def run_source_collection(self, limit: Optional[int] = None, dry_run: bool = False, **kwargs) -> DummyBatchResult:
        return DummyBatchResult(processed_count=0, success_count=0)

class HousekeepingRunner:
    def run_housekeeping(self, dry_run: bool = False, **kwargs) -> DummyBatchResult:
        return DummyBatchResult(processed_count=0, success_count=0)

class ListingExecutionRunner:
    def run_execution(self, dry_run: bool = False, **kwargs) -> DummyBatchResult:
        return DummyBatchResult(processed_count=0, success_count=0)
