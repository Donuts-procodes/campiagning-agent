from abc import ABC, abstractmethod
from typing import Any

from src.models.campaign_state import ExecutionReceipt


class BaseAdapter(ABC):
    @abstractmethod
    def dispatch(self, mode: str, payload: dict[str, Any]) -> ExecutionReceipt:
        """
        Dispatches the payload based on execution mode.
        Modes: 'dry_run', 'task_queue', 'csv_export', 'webhook'
        """
