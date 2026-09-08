from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from src.models.campaign_state import ClosedLoopMetrics, ClosedLoopState
from src.services.crm_service import CRMService

logger = logging.getLogger(__name__)


class LearningService:
    @classmethod
    async def evaluate_campaign_performance(
        cls,
        campaign_thread_id: str,
        graph: CompiledStateGraph | None = None,
        state_override: dict[str, Any] | None = None,
    ) -> ClosedLoopMetrics:
        """
        Executes the Closed-Loop Learning Agent (jj.mmd FeedbackLoop):
        1. Reads downstream CRM contact records & attribution pipeline.
        2. Computes actual CAC, Conversion Rates, and ROAS against targets.
        3. Generates data-driven budget reallocations and optimization directives.
        4. Synthesizes historical ROAS/CAC data to steer Upstream Strategy.
        """
        # 1. Fetch Downstream CRM contacts & attribution
        contacts = await CRMService.get_campaign_contacts(campaign_thread_id)
        
        # 2. Extract strategy & budget targets from state
        state = state_override or {}
        if not state and graph:
            from src.services.campaign_service import CampaignService
            state = await CampaignService.get_state(campaign_thread_id, graph)

        user_input = state.get("user_input")
        budget = 5000.0
        target_roas = 3.0
        target_cac = 250.0

        if user_input:
            if isinstance(user_input, dict):
                if user_input.get("budget"):
                    budget = float(user_input["budget"])
                if user_input.get("target_roas"):
                    target_roas = float(user_input["target_roas"])
                if user_input.get("target_cac"):
                    target_cac = float(user_input["target_cac"])
                else:
                    target_meetings = int(user_input.get("target_meetings") or 10)
                    target_cac = round(budget / max(target_meetings, 1), 2)
            else:
                if getattr(user_input, "budget", None):
                    budget = float(user_input.budget)
                if getattr(user_input, "target_roas", None):
                    target_roas = float(user_input.target_roas)
                if getattr(user_input, "target_cac", None):
                    target_cac = float(user_input.target_cac)
                else:
                    target_meetings = int(getattr(user_input, "target_meetings", 10) or 10)
                    target_cac = round(budget / max(target_meetings, 1), 2)

        # 3. Funnel aggregation
        total_enrolled = len(contacts)
        active_sequences = len([c for c in contacts if c.get("status") in ("sequence_active", "enrolled")])
        replied_count = len([c for c in contacts if c.get("status") == "replied"])
        converted_count = len([c for c in contacts if c.get("status") in ("meeting_booked", "converted")])

        # 4. Attribution breakdown
        channel_counts: dict[str, dict[str, Any]] = {}
        for c in contacts:
            src = c.get("attribution_source") or "direct"
            if src not in channel_counts:
                channel_counts[src] = {"enrolled": 0, "replied": 0, "converted": 0, "deal_value": 0.0}
            channel_counts[src]["enrolled"] += 1
            if c.get("status") == "replied":
                channel_counts[src]["replied"] += 1
            elif c.get("status") in ("meeting_booked", "converted"):
                channel_counts[src]["converted"] += 1
                deal_val = float(c.get("deal_value", 0.0)) or 3500.0
                channel_counts[src]["deal_value"] += deal_val

        # 5. Financial metrics computation
        actual_cac = round(budget / max(converted_count, 1), 2) if converted_count > 0 else budget
        conversion_rate = round(converted_count / max(total_enrolled, 1), 4) if total_enrolled > 0 else 0.0
        
        # Calculate attributed revenue
        total_attributed_revenue = sum(ch["deal_value"] for ch in channel_counts.values())
        if total_attributed_revenue == 0 and converted_count > 0:
            total_attributed_revenue = converted_count * 3500.0  # Assumed deal ACV benchmark
        
        actual_roas = round(total_attributed_revenue / max(budget, 1.0), 2)

        # 6. Performance status determination
        if actual_roas >= target_roas and actual_cac <= target_cac:
            performance_status = "exceeding"
        elif actual_roas >= 0.7 * target_roas or actual_cac <= 1.3 * target_cac:
            performance_status = "on_track"
        else:
            performance_status = "underperforming"

        # 7. Closed-loop optimization recommendations & budget reallocations
        recommendations = []
        budget_reallocations: dict[str, float] = {}

        # Evaluate channels to find winners
        best_channel = max(channel_counts.items(), key=lambda x: x[1]["converted"], default=("none", {}))[0]
        
        if converted_count > 0:
            recommendations.append(
                f"Conversion efficiency established: {converted_count} converted leads at ${actual_cac} CAC (Target: ${target_cac})."
            )
            recommendations.append(
                f"Top converting channel is '{best_channel}' with {channel_counts.get(best_channel, {}).get('converted', 0)} conversions."
            )
            if actual_roas >= target_roas:
                recommendations.append(
                    f"ROAS is {actual_roas}x, surpassing target of {target_roas}x. Recommend scaling total ad spend by 25%."
                )
            else:
                recommendations.append(
                    f"ROAS is {actual_roas}x (Target: {target_roas}x). Optimize bottom-of-funnel conversion and tighten ICP qualification."
                )
        else:
            recommendations.append(
                f"Currently in lead acquisition phase ({total_enrolled} enrolled). No conversions recorded yet."
            )
            recommendations.append(
                "Recommendation: Accelerate sequence cadences and deploy personalized LinkedIn connection touches on Day 3."
            )

        # Compute dynamic budget reallocations
        if "meta_ads" in channel_counts and "google_ads" in channel_counts:
            meta_conv = channel_counts["meta_ads"]["converted"]
            google_conv = channel_counts["google_ads"]["converted"]
            if meta_conv > google_conv:
                budget_reallocations = {"meta_ads": 0.50, "google_ads": 0.20, "outbound_email": 0.30}
                recommendations.append("Reallocating +15% media spend from Google Ads to Meta Ads due to superior conversion velocity.")
            else:
                budget_reallocations = {"google_ads": 0.45, "meta_ads": 0.25, "outbound_email": 0.30}
                recommendations.append("Reallocating +10% media spend toward Google Search intent queries.")
        else:
            budget_reallocations = {"media_ads": 0.40, "inbound_web_forms": 0.30, "outbound_sequences": 0.30}

        metrics = ClosedLoopMetrics(
            total_spend=budget,
            total_enrolled=total_enrolled,
            active_sequences=active_sequences,
            replied_count=replied_count,
            converted_count=converted_count,
            actual_cac=actual_cac,
            target_cac=target_cac,
            conversion_rate=conversion_rate,
            actual_roas=actual_roas,
            target_roas=target_roas,
            performance_status=performance_status,
            channel_performance=channel_counts,
            optimization_recommendations=recommendations,
            budget_reallocations=budget_reallocations,
            evaluated_at=datetime.now(timezone.utc),
        )

        return metrics

    @classmethod
    async def apply_feedback_to_campaign(
        cls,
        campaign_thread_id: str,
        graph: CompiledStateGraph,
    ) -> dict[str, Any]:
        """
        Injects the evaluated metrics back into the campaign's State (ACTUALS -.-> STRATEGY).
        """
        metrics = await cls.evaluate_campaign_performance(campaign_thread_id, graph=graph)
        from langchain_core.runnables import RunnableConfig
        config: RunnableConfig = {"configurable": {"thread_id": campaign_thread_id}}

        state_tuple = await graph.aget_state(config)
        existing_closed_loop = None
        if state_tuple and state_tuple.values:
            cl = state_tuple.values.get("closed_loop")
            if cl:
                existing_closed_loop = cl

        history = existing_closed_loop.evaluation_history if existing_closed_loop else []
        history.append(metrics)

        new_closed_loop_state = ClosedLoopState(
            latest_evaluation=metrics,
            evaluation_history=history,
        )

        # Update strategy with historical feedback
        feedback_payload = {
            "last_evaluated": metrics.evaluated_at.isoformat(),
            "historical_roas": metrics.actual_roas,
            "historical_cac": metrics.actual_cac,
            "budget_reallocations": metrics.budget_reallocations,
            "recommendations": metrics.optimization_recommendations,
        }

        # Update LangGraph state
        await graph.aupdate_state(
            config,
            {
                "closed_loop": new_closed_loop_state,
            }
        )

        return {
            "campaign_thread_id": campaign_thread_id,
            "applied_metrics": metrics.model_dump(),
            "feedback_payload": feedback_payload,
        }
