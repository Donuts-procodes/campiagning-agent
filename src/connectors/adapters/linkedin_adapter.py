import logging
from datetime import datetime
from typing import Any

from src.connectors.adapters.base_adapter import BaseAdapter
from src.models.campaign_state import ExecutionReceipt

logger = logging.getLogger(__name__)

class LinkedInAdapter(BaseAdapter):
    def dispatch(self, mode: str, payload: dict[str, Any]) -> ExecutionReceipt:
        logger.info(f"Dispatching linkedin via {mode} mode")
        
        status = "dispatched"
        if mode == "dry_run":
            status = "skipped"
        elif mode == "csv_export":
            status = "exported"
            
        return ExecutionReceipt(
            channel="linkedin",
            job_id=f"linkedin_{mode}_{int(datetime.utcnow().timestamp())}",
            contacts_enrolled=payload.get("volume", 0),
            status=status,
            dispatched_at=datetime.utcnow() if status == "dispatched" else None,
            response_payload={"mode": mode, "details": "Mock linkedin dispatch"}
        )
