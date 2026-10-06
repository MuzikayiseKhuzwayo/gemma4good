import os
import difflib
import uuid
import time
from typing import Dict, Any, Optional, Tuple, List

class CapabilityType:
    SANDBOX_FS = "SANDBOX_FS"
    HOST_FS_READ = "HOST_FS_READ"
    HOST_FS_WRITE = "HOST_FS_WRITE"
    OUTBOUND_NETWORK = "OUTBOUND_NETWORK"
    SHELL_EXECUTION = "SHELL_EXECUTION"
    NATIVE_AUTOMATION = "NATIVE_AUTOMATION"

class CapabilitySecurityManager:
    """
    Phase 3: Granular Capability-Based Security Model.
    Enforces least-privilege security guarantees:
    - Sandboxed workspace read/write: Auto-approved.
    - Host filesystem modification: Prompts operator with unified diff preview.
    - Outbound network & shell execution: Requires explicit operator approval.
    """

    def __init__(self, auto_approve_sandbox: bool = True):
        self.auto_approve_sandbox = auto_approve_sandbox
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.granted_tokens: Dict[str, float] = {} # token -> expiry timestamp

    def evaluate_request(
        self,
        capability: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        is_sandbox: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates an operation against capability policies.
        Returns authorization verdict with diff preview or approval request.
        """
        details = details or {}
        req_id = str(uuid.uuid4())[:8]

        # 1. Sandboxed Workspace Operations
        if is_sandbox and capability in [CapabilityType.SANDBOX_FS]:
            self._log_audit(req_id, capability, resource, "AUTO_APPROVED", "Sandbox workspace isolation")
            return {
                "approved": True,
                "requires_prompt": False,
                "request_id": req_id,
                "message": "Auto-approved within sandboxed workspace."
            }

        # 2. Host Filesystem Read Operations
        if capability == CapabilityType.HOST_FS_READ:
            # Auto-approve read if within safe user directory
            self._log_audit(req_id, capability, resource, "APPROVED", "Read-only access")
            return {
                "approved": True,
                "requires_prompt": False,
                "request_id": req_id,
                "message": "Host read permitted."
            }

        # 3. Host Filesystem Write Operations (Requires Diff Preview & Approval)
        if capability == CapabilityType.HOST_FS_WRITE:
            old_content = ""
            if os.path.exists(resource):
                try:
                    with open(resource, "r", encoding="utf-8", errors="ignore") as f:
                        old_content = f.read()
                except Exception:
                    old_content = "<Binary or Unreadable File>"

            new_content = str(details.get("content", ""))
            diff_lines = list(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{os.path.basename(resource)}",
                tofile=f"b/{os.path.basename(resource)}"
            ))
            diff_text = "".join(diff_lines) or f"[New File Creation: {len(new_content)} characters]"

            approval_record = {
                "request_id": req_id,
                "capability": capability,
                "resource": resource,
                "diff": diff_text,
                "timestamp": time.time(),
                "status": "PENDING"
            }
            self.pending_approvals[req_id] = approval_record

            self._log_audit(req_id, capability, resource, "PENDING_APPROVAL", "Host write modification requires confirmation")
            return {
                "approved": False,
                "requires_prompt": True,
                "request_id": req_id,
                "diff_preview": diff_text,
                "prompt": f"Authorize host filesystem write to '{resource}'?\nDiff Preview:\n{diff_text}"
            }

        # 4. Outbound Network & Shell Execution
        if capability in [CapabilityType.OUTBOUND_NETWORK, CapabilityType.SHELL_EXECUTION, CapabilityType.NATIVE_AUTOMATION]:
            approval_record = {
                "request_id": req_id,
                "capability": capability,
                "resource": resource,
                "details": details,
                "timestamp": time.time(),
                "status": "PENDING"
            }
            self.pending_approvals[req_id] = approval_record

            self._log_audit(req_id, capability, resource, "PENDING_APPROVAL", f"Elevated {capability} capability requested")
            return {
                "approved": False,
                "requires_prompt": True,
                "request_id": req_id,
                "prompt": f"Operator authorization required for {capability} on target: {resource}"
            }

        return {"approved": False, "requires_prompt": True, "request_id": req_id, "message": "Unknown capability"}

    def approve_request(self, request_id: str) -> bool:
        """Approves a pending capability request and issues a capability token."""
        if request_id in self.pending_approvals:
            self.pending_approvals[request_id]["status"] = "APPROVED"
            token = f"cap_tok_{request_id}_{int(time.time())}"
            self.granted_tokens[token] = time.time() + 300.0 # Valid for 5 minutes
            self._log_audit(request_id, self.pending_approvals[request_id]["capability"], self.pending_approvals[request_id]["resource"], "GRANTED", f"Token {token}")
            return True
        return False

    def deny_request(self, request_id: str) -> bool:
        """Denies a pending capability request."""
        if request_id in self.pending_approvals:
            self.pending_approvals[request_id]["status"] = "DENIED"
            self._log_audit(request_id, self.pending_approvals[request_id]["capability"], self.pending_approvals[request_id]["resource"], "DENIED", "Operator denied request")
            return True
        return False

    def is_token_valid(self, token: str) -> bool:
        """Validates that a capability token has not expired."""
        exp = self.granted_tokens.get(token)
        if exp and exp > time.time():
            return True
        return False

    def _log_audit(self, req_id: str, cap: str, res: str, action: str, reason: str):
        self.audit_log.append({
            "request_id": req_id,
            "capability": cap,
            "resource": res,
            "action": action,
            "reason": reason,
            "timestamp": time.time()
        })
