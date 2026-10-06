import json
from typing import List, Dict, Any, Optional

class GenerativeUIDSL:
    """
    Phase 4: Declarative Dynamic UI DSL.
    Emits structured JSON schemas for frontend dynamic compositing:
    - Tables
    - Charts (bar, line, metric)
    - Approval Cards (diff previews + actions)
    - Audio Players (ambient voice feedback)
    - Telemetry / Swarm Tiles
    """

    @staticmethod
    def table(title: str, columns: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
        return {
            "widget": "TABLE",
            "title": title,
            "columns": columns,
            "rows": rows
        }

    @staticmethod
    def chart(title: str, chart_type: str, labels: List[str], values: List[float], unit: str = "") -> Dict[str, Any]:
        return {
            "widget": "CHART",
            "title": title,
            "chart_type": chart_type, # 'bar', 'line', 'metric'
            "labels": labels,
            "values": values,
            "unit": unit
        }

    @staticmethod
    def approval_card(request_id: str, capability: str, resource: str, diff_preview: str) -> Dict[str, Any]:
        return {
            "widget": "APPROVAL_CARD",
            "request_id": request_id,
            "capability": capability,
            "resource": resource,
            "diff_preview": diff_preview
        }

    @staticmethod
    def audio_player(title: str, text_content: str, auto_play: bool = True) -> Dict[str, Any]:
        return {
            "widget": "AUDIO_PLAYER",
            "title": title,
            "text_content": text_content,
            "auto_play": auto_play
        }

    @staticmethod
    def telemetry_tile(title: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "widget": "STATUS_TILE",
            "title": title,
            "metrics": metrics
        }
