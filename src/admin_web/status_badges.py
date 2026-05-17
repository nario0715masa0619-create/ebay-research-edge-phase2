class StatusBadgeMapper:
    @staticmethod
    def get_candidate_class(status: str) -> str:
        s = status.lower()
        if s in ["listed"]:
            return "badge-success"
        elif s in ["collected", "listing_in_progress"]:
            return "badge-info"
        elif s in ["failed"]:
            return "badge-error"
        elif s in ["withdrawn", "excluded"]:
            return "badge-warning"
        return "badge-secondary"

    @staticmethod
    def get_readiness_class(readiness: str) -> str:
        r = readiness.lower()
        if r in ["ready"]:
            return "badge-success"
        elif r in ["blocked"]:
            return "badge-error"
        elif r in ["not_checked", "checking"]:
            return "badge-warning"
        return "badge-secondary"

    @staticmethod
    def get_job_class(status: str) -> str:
        s = status.lower()
        if s in ["success", "completed"]:
            return "badge-success"
        elif s in ["running", "pending"]:
            return "badge-info"
        elif s in ["failed", "fatal"]:
            return "badge-error"
        elif s in ["warning", "warn", "skipped"]:
            return "badge-warning"
        return "badge-secondary"

    @staticmethod
    def get_notification_class(severity: str) -> str:
        s = severity.lower()
        if s in ["critical", "error", "fatal"]:
            return "badge-error"
        elif s in ["warning", "warn"]:
            return "badge-warning"
        elif s in ["info", "success"]:
            return "badge-success"
        return "badge-info"
