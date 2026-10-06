import json
import time
from typing import Generator, Dict, Any, List

class GenerativeUIStreamRenderer:
    """
    Phase 4: Generative UI Stream Renderer.
    Encodes token streams, reasoning chains, and dynamic UI DSL widgets
    into standard Server-Sent Events (SSE) format: 'data: {...}\\n\\n'.
    """

    @staticmethod
    def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
        """Formats a dictionary payload into an SSE data line."""
        envelope = {
            "event": event_type,
            "timestamp": time.time(),
            "data": data
        }
        return f"data: {json.dumps(envelope)}\n\n"

    @classmethod
    def stream_tokens(cls, tokens: List[str]) -> Generator[str, None, None]:
        """Streams individual reasoning or generation tokens."""
        for token in tokens:
            yield cls.format_sse_event("token", {"token": token})

    @classmethod
    def stream_widget(cls, widget_spec: Dict[str, Any]) -> str:
        """Emits a dynamic declarative UI DSL widget to the client compositor."""
        return cls.format_sse_event("widget", widget_spec)

    @classmethod
    def stream_intent_execution(cls, intent_type: str, status: str, result: Any) -> str:
        """Emits live intent execution updates."""
        return cls.format_sse_event("execution", {
            "intent_type": intent_type,
            "status": status,
            "result": str(result)
        })
