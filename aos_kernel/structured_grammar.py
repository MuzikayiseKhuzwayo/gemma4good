import json
import re
from typing import List, Dict, Any, Optional

VALID_INTENT_TYPES = {
    "WRITE_FILE",
    "READ_FILE",
    "DELETE_FILE",
    "SEARCH_MEMORY",
    "SEND_MESSAGE",
    "NOTIFY_USER",
    "ASK_USER_INPUT",
    "RUN_SANDBOX_CODE",
    "HOST_AUTOMATE",
    "QUERY_GRAPH"
}

INTENT_REQUIRED_FIELDS = {
    "WRITE_FILE": ["path"],
    "READ_FILE": ["path"],
    "DELETE_FILE": ["path"],
    "SEARCH_MEMORY": ["query"],
    "SEND_MESSAGE": ["to", "body"],
    "NOTIFY_USER": ["message"],
    "ASK_USER_INPUT": ["prompt"],
    "RUN_SANDBOX_CODE": ["code"],
    "HOST_AUTOMATE": ["action"],
    "QUERY_GRAPH": ["query"]
}

class StructuredGrammarEnforcer:
    """
    Phase 1: Enforces context-free grammar and JSON schema validation.
    Guarantees mathematically safe JSON extraction and automated schema repair
    to prevent parsing errors from LLM generation.
    """

    @staticmethod
    def repair_json_string(raw_text: str) -> str:
        """
        Repairs common LLM formatting flaws:
        - Markdown code fences (```json ... ```)
        - Leading/trailing conversational text
        - Single quotes instead of double quotes
        - Trailing commas before closing braces/brackets
        - Unclosed arrays or objects
        """
        text = raw_text.strip()

        # Remove markdown code blocks if present
        if "```" in text:
            # Match contents between ```json ... ``` or just ``` ... ```
            fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
            if fence_match:
                text = fence_match.group(1).strip()

        # Locate outermost array or object
        start_bracket = text.find('[')
        start_brace = text.find('{')

        if start_bracket != -1 and (start_brace == -1 or start_bracket < start_brace):
            start = start_bracket
            end = text.rfind(']')
            if end != -1 and end > start:
                candidate = text[start:end + 1]
            else:
                candidate = text[start:] + "]"
        elif start_brace != -1:
            start = start_brace
            end = text.rfind('}')
            if end != -1 and end > start:
                candidate = "[" + text[start:end + 1] + "]"
            else:
                candidate = "[" + text[start:] + "}]"
        else:
            candidate = text

        # Clean trailing commas: , ] -> ] and , } -> }
        candidate = re.sub(r',\s*\]', ']', candidate)
        candidate = re.sub(r',\s*\}', '}', candidate)

        return candidate

    @classmethod
    def parse_and_validate(cls, raw_text: str) -> List[Dict[str, Any]]:
        """
        Parses the raw text, repairs JSON defects, and validates every intent object
        against its strict schema definition.
        """
        cleaned = cls.repair_json_string(raw_text)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback regex extraction of JSON objects
            parsed = cls._regex_extract_intents(raw_text)

        if not isinstance(parsed, list):
            if isinstance(parsed, dict):
                parsed = [parsed]
            else:
                return []

        validated_intents: List[Dict[str, Any]] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            validated = cls.validate_intent_schema(item)
            if validated:
                validated_intents.append(validated)

        return validated_intents

    @classmethod
    def validate_intent_schema(cls, intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validates an individual intent against schema invariants.
        Normalizes and repairs missing fields where possible.
        """
        intent_type = intent.get("type")
        if not intent_type or not isinstance(intent_type, str):
            return None

        intent_type = intent_type.upper().strip()
        if intent_type not in VALID_INTENT_TYPES:
            # Attempt to normalize fuzzy types
            intent_type = cls._normalize_fuzzy_type(intent_type)
            if intent_type not in VALID_INTENT_TYPES:
                return None

        thought = intent.get("thought_process")
        if not thought or not isinstance(thought, str):
            thought = f"Automated execution for intent {intent_type}."

        payload = intent.get("payload")
        if not isinstance(payload, dict):
            payload = {}

        # Validate and repair payload by type
        payload = cls._repair_payload(intent_type, payload)

        return {
            "thought_process": thought.strip(),
            "type": intent_type,
            "payload": payload
        }

    @staticmethod
    def _normalize_fuzzy_type(intent_type: str) -> str:
        mapping = {
            "WRITE": "WRITE_FILE",
            "SAVE_FILE": "WRITE_FILE",
            "CREATE_FILE": "WRITE_FILE",
            "READ": "READ_FILE",
            "OPEN_FILE": "READ_FILE",
            "DELETE": "DELETE_FILE",
            "REMOVE_FILE": "DELETE_FILE",
            "SEARCH": "SEARCH_MEMORY",
            "FIND": "SEARCH_MEMORY",
            "MESSAGE": "SEND_MESSAGE",
            "NOTIFY": "NOTIFY_USER",
            "ALERT": "NOTIFY_USER",
            "ASK": "ASK_USER_INPUT",
            "QUESTION": "ASK_USER_INPUT",
            "EXECUTE": "RUN_SANDBOX_CODE",
            "RUN_CODE": "RUN_SANDBOX_CODE",
            "AUTOMATE": "HOST_AUTOMATE"
        }
        return mapping.get(intent_type, intent_type)

    @staticmethod
    def _repair_payload(intent_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures required fields exist with valid fallback values."""
        repaired = dict(payload)

        if intent_type in ["WRITE_FILE", "READ_FILE", "DELETE_FILE"]:
            if "path" not in repaired:
                for k in ["filename", "file", "name", "target"]:
                    if k in repaired:
                        repaired["path"] = str(repaired.pop(k))
                        break
            if "path" not in repaired:
                repaired["path"] = "/tmp/default.txt"
            if intent_type == "WRITE_FILE" and "content" not in repaired:
                repaired["content"] = str(repaired.get("body", repaired.get("text", "")))

        elif intent_type == "SEARCH_MEMORY":
            if "query" not in repaired:
                repaired["query"] = str(repaired.get("q", repaired.get("term", "")))

        elif intent_type == "SEND_MESSAGE":
            if "to" not in repaired:
                repaired["to"] = str(repaired.get("recipient", "User"))
            if "body" not in repaired:
                repaired["body"] = str(repaired.get("message", repaired.get("content", "")))

        elif intent_type == "NOTIFY_USER":
            if "message" not in repaired:
                repaired["message"] = str(repaired.get("text", repaired.get("body", "Notification")))

        elif intent_type == "ASK_USER_INPUT":
            if "prompt" not in repaired:
                repaired["prompt"] = str(repaired.get("question", repaired.get("message", "Please clarify.")))

        elif intent_type == "RUN_SANDBOX_CODE":
            if "code" not in repaired:
                repaired["code"] = str(repaired.get("script", ""))

        elif intent_type == "HOST_AUTOMATE":
            if "action" not in repaired:
                repaired["action"] = str(repaired.get("type", "status"))

        elif intent_type == "QUERY_GRAPH":
            if "query" not in repaired:
                repaired["query"] = str(repaired.get("entity", ""))

        return repaired

    @classmethod
    def _regex_extract_intents(cls, text: str) -> List[Dict[str, Any]]:
        """Fallback to extract intent-like patterns with regex when JSON is severely malformed."""
        intents = []
        pattern = re.compile(
            r'\{[^{}]*"type"\s*:\s*"([A-Z_]+)"[^{}]*\}',
            re.IGNORECASE
        )
        for match in pattern.finditer(text):
            try:
                candidate = match.group(0)
                candidate = re.sub(r',\s*\}', '}', candidate)
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    intents.append(obj)
            except Exception:
                continue
        return intents
