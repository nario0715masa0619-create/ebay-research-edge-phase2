from typing import Dict, Set
import threading

class JobLockManager:
    """
    Manages in-memory locks for jobs to prevent overlapping executions.
    """
    def __init__(self):
        self._locks: Set[str] = set()
        self._mutex = threading.Lock()

    def acquire(self, lock_key: str) -> bool:
        with self._mutex:
            if lock_key in self._locks:
                return False
            self._locks.add(lock_key)
            return True

    def release(self, lock_key: str):
        with self._mutex:
            if lock_key in self._locks:
                self._locks.remove(lock_key)

    def is_locked(self, lock_key: str) -> bool:
        with self._mutex:
            return lock_key in self._locks
