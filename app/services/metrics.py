from app.repositories import EscalationRepository, SupportRequestRepository
from app.schemas.admin import DashboardOut, EscalationsOut, LogsOut


class MetricsService:
    """Метрики и логи из реальных данных (SupportRequest / Escalation)."""

    def __init__(
        self,
        support_repo: SupportRequestRepository,
        escalation_repo: EscalationRepository,
    ) -> None:
        self._support = support_repo
        self._escalations = escalation_repo

    def dashboard(self) -> DashboardOut:
        total = self._support.count()
        escalated = self._escalations.count()
        success = max(total - escalated, 0)
        return DashboardOut(
            total_requests=total,
            success_rate=round(success * 100 / total, 1) if total else 0.0,
            avg_response_ms=round(self._support.avg_response_ms()),
            escalations=escalated,
        )

    def escalations(self) -> EscalationsOut:
        items = self._escalations.list_recent()
        return EscalationsOut(items=items, total=len(items))

    def logs(self) -> LogsOut:
        items = self._support.list_recent()
        return LogsOut(items=items, total=len(items))