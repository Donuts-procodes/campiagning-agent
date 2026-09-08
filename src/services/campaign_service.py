from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import BackgroundTasks
from langgraph.graph.state import CompiledStateGraph

from src.models.campaign import HITLDecision
from src.models.campaign_state import UserInputState

logger = logging.getLogger(__name__)

from langchain_core.runnables import RunnableConfig


class CampaignService:
    @staticmethod
    async def _run_graph_background(graph: CompiledStateGraph, config: RunnableConfig, input_data: dict | None = None):
        import json

        from src.core.database import get_redis_client
        redis_client = get_redis_client()
        thread_id = config["configurable"]["thread_id"]
        channel = f"campaign_updates:{thread_id}"
        
        try:
            async for output in graph.astream(input_data, config, stream_mode="updates"):
                await redis_client.publish(channel, json.dumps({"status": "updated"}))
            # Publish final completion
            await redis_client.publish(channel, json.dumps({"status": "completed"}))
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            try:
                await graph.aupdate_state(config, {"error": str(e)})
            except Exception as update_err:
                logger.error(f"Failed to update state with error: {update_err}")
            finally:
                await redis_client.publish(channel, json.dumps({"status": "error", "message": str(e)}))

    @staticmethod
    async def create_campaign(
        user_input: UserInputState,
        background_tasks: BackgroundTasks,
        graph: CompiledStateGraph
    ) -> dict[str, Any]:
        thread_id = str(uuid.uuid4())
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        
        # Dual-Mode Target Prospect Sourcing
        from src.services.crm_service import CRMService
        if user_input.initial_contacts:
            # Mode A: User uploaded CSV / explicit contact list
            await CRMService.bulk_enroll_contacts(thread_id, user_input.initial_contacts)
        elif user_input.prospect_sourcing_mode == "ai_sourcing":
            # Mode B: Autonomous AI prospect discovery matching ICP
            await CRMService.autonomous_prospect_sourcing(
                campaign_thread_id=thread_id,
                company_name=user_input.company_name,
                target_icp=user_input.target_icp,
                target_geography=user_input.target_geography,
            )

        # Start graph execution in background
        background_tasks.add_task(
            CampaignService._run_graph_background,
            graph,
            config,
            {"user_input": user_input}
        )
        return {"thread_id": thread_id, "status": "started"}

    @staticmethod
    async def get_state(thread_id: str, graph: CompiledStateGraph) -> dict[str, Any]:
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        state_tuple = await graph.aget_state(config)
        if not state_tuple or not state_tuple.values:
            return {}
            
        values = dict(state_tuple.values)
        next_nodes = list(state_tuple.next or [])
        values["next_nodes"] = next_nodes
        values["next"] = next_nodes

        return values

    @staticmethod
    async def approve_campaign(
        thread_id: str,
        decision: HITLDecision,
        background_tasks: BackgroundTasks,
        graph: CompiledStateGraph
    ) -> dict[str, Any]:
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        
        from src.models.campaign_state import HITLState
        
        hitl_state = HITLState(
            approved_variant_id=decision.approved_variant_id,
            human_modifications=decision.human_modifications or {},
            review_status=decision.review_status
        )

        # Inject the decision directly into the state at the hitl_approval_node
        await graph.aupdate_state(
            config,
            {"hitl": hitl_state},
            as_node="hitl_approval_node"
        )
        
        # Resume execution
        background_tasks.add_task(
            CampaignService._run_graph_background,
            graph,
            config,
            None
        )
        
        return {"thread_id": thread_id, "status": "resumed"}

    @staticmethod
    async def get_receipts(thread_id: str, graph: CompiledStateGraph) -> dict[str, Any]:
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        state_tuple = await graph.aget_state(config)
        
        if state_tuple and state_tuple.values:
            execution = state_tuple.values.get("execution")
            if execution:
                if hasattr(execution, "model_dump"):
                    return execution.model_dump()
                return {"receipts": execution.get("receipts", [])}
                
        return {"receipts": []}
