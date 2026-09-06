from app.schemas.admin import DashboardOut, EscalationsOut, LogsOut


class MetricsService:
    """Метрики и логи.

    TODO(Фаза 6): считать реальные значения из SupportRequest/Escalation (БД).
    На 0-й фазе — валидные нулевые контракты.
    """

    def dashboard(self) -> DashboardOut:
        return DashboardOut()

    def escalations(self) -> EscalationsOut:
        return EscalationsOut(items=[], total=0)

    def logs(self) -> LogsOut:
        return LogsOut(items=[], total=0)
