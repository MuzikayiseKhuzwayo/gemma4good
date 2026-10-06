import time
import json
from typing import List, Dict, Any, Optional
from semantic_fs.vector_store import SemanticFileSystem

class ContextBudgetManager:
    """
    Phase 2: 3-Tier Hierarchical Context Paging System.
    
    Memory Tiers:
    - Tier 1 (L1): Active Context Window (Fast Working Memory, 0-8192 tokens)
    - Tier 2 (L2): Compressed Episodic Memory (Summarized Task Graphs & Reason Chains)
    - Tier 3 (L3): Persistent Semantic Vector Storage & Knowledge Graph (Disk-backed RAG)
    """

    def __init__(self, max_tokens: int = 8192, sfs: Optional[SemanticFileSystem] = None):
        self.max_tokens = max_tokens
        self.current_usage = 0
        self.active_context: List[str] = [] # L1 Working Memory
        self.l2_episodic_memory: List[Dict[str, Any]] = [] # L2 Compressed Cache
        self.sfs = sfs
        self.stats = {
            "page_faults": 0,
            "context_swaps": 0,
            "l2_evictions": 0
        }

    def add_intent(self, intent_tokens: int = 150):
        """Monitors token usage and triggers paging swap if window saturates."""
        if self.current_usage + intent_tokens > self.max_tokens:
            self._swap_context()
        self.current_usage += intent_tokens

    def append_l1(self, entry: str):
        """Appends a turn or reasoning step to L1 working memory."""
        self.active_context.append(entry)
        self.add_intent(len(entry.split()) * 2)

    def _swap_context(self):
        """
        Pages older L1 reasoning traces down to L2 Compressed Episodic Memory,
        and archives key facts to L3 Semantic Vector Storage.
        """
        self.stats["context_swaps"] += 1
        print("[ContextManager] Page Eviction Triggered: Swapping L1 Working Memory to L2/L3...")

        if len(self.active_context) > 5:
            # Stale context to compress
            stale_slice = self.active_context[:-5]
            summary_entry = {
                "timestamp": time.time(),
                "compressed_trace": " | ".join(stale_slice),
                "summary": f"Compressed session of {len(stale_slice)} steps: {stale_slice[0][:80]}..."
            }
            self.l2_episodic_memory.append(summary_entry)

            # Persist to L3 Semantic File System if available
            if self.sfs:
                doc_path = f"/memory/l2_swap_{int(time.time())}.txt"
                self.sfs.vectorize_and_store(
                    doc_path,
                    summary_entry["compressed_trace"],
                    metadata={"type": "episodic_memory", "timestamp": time.time()}
                )

            # Retain only the most recent working turns in L1
            self.active_context = self.active_context[-5:]
            self.current_usage = sum(len(x.split()) * 2 for x in self.active_context)
        else:
            self.current_usage = 0

    def page_fault(self, query: str, top_k: int = 3) -> List[str]:
        """
        Resolves a Context Page Fault:
        When the model needs older context not present in L1,
        it queries L2 Episodic Memory and L3 Semantic Storage,
        paging relevant context back into active working memory.
        """
        self.stats["page_faults"] += 1
        paged_memories = []

        # 1. Search L2 Episodic Memory
        q_lower = query.lower()
        for ep in reversed(self.l2_episodic_memory):
            if any(term in ep["compressed_trace"].lower() for term in q_lower.split()):
                paged_memories.append(f"[Paged from L2]: {ep['summary']}")
                if len(paged_memories) >= top_k:
                    break

        # 2. Search L3 Semantic Storage
        if self.sfs and len(paged_memories) < top_k:
            l3_hits = self.sfs.retrieve(query, top_k=top_k - len(paged_memories))
            for hit in l3_hits:
                snippet = hit["content"][:150]
                paged_memories.append(f"[Paged from L3 ({hit['path']})]: {snippet}")

        if paged_memories:
            print(f"[ContextManager] Page Fault Resolved: Restored {len(paged_memories)} memory segments into L1.")
            for mem in paged_memories:
                self.active_context.insert(0, mem)

        return paged_memories

    def get_memory_stats(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry for the 3 memory tiers."""
        return {
            "l1_active_turns": len(self.active_context),
            "l1_token_usage": self.current_usage,
            "l1_max_budget": self.max_tokens,
            "l2_episodic_entries": len(self.l2_episodic_memory),
            "total_page_faults": self.stats["page_faults"],
            "total_swaps": self.stats["context_swaps"]
        }
