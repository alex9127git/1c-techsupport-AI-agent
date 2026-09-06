from app.repositories import SettingsRepository


class SettingsService:
    """Рабочий сервис настроек (не заглушка).

    Порог уверенности и стратегия эскалации берутся из БД (таблица settings),
    а при отсутствии значения — из типизированного конфига (.env / дефолты).
    От этих значений в Фазе 1 зависит логика эскалации.
    """

    def __init__(self, settings_repo: SettingsRepository) -> None:
        self._repo = settings_repo

    def get_threshold(self, default: int = 80) -> int:
        try:
            return int(self._repo.get("confidence_threshold", str(default)))
        except (TypeError, ValueError):
            return default

    def get_strategy(self, default: str = "human_review") -> str:
        return self._repo.get("escalation_strategy", default) or default

    def as_dict(self, default_threshold: int = 80, default_strategy: str = "human_review") -> dict:
        return {
            "confidence_threshold": self.get_threshold(default_threshold),
            "escalation_strategy": self.get_strategy(default_strategy),
        }

    def update(self, threshold: int | None, strategy: str | None) -> dict:
        if threshold is not None:
            self._repo.set("confidence_threshold", str(threshold))
        if strategy:
            self._repo.set("escalation_strategy", strategy)
        return self.as_dict()
