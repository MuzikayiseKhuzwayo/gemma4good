import asyncio
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from aos_kernel.context_manager import ContextBudgetManager
from aos_kernel.inference import GemmaLatentKernel

class AOSDaemon:
    """
    Upgraded Autonomous Daemon of the Agentic Operating System.
    Orchestrates the interactive ReAct loop with:
    - Speculative Dual-Kernel routing
    - 3-Tier Hierarchical Context Paging
    - Capability-Gated Shell Agent Execution
    """

    def __init__(self, fs=None, agent=None, inference_engine=None):
        self.fs = fs
        self.agent = agent
        self.context_manager = ContextBudgetManager(sfs=fs)
        self.inference_engine = inference_engine or GemmaLatentKernel(mode="google_genai")
        self.running = False

    async def run(self):
        self.running = True
        print("\nAOS Daemon running. Entering Interactive Mode...")
        print("Type 'exit' or 'quit' to shutdown.\n")

        while self.running:
            try:
                user_input = await asyncio.to_thread(input, "AOS> ")
            except EOFError:
                break

            if user_input.lower().strip() in ['exit', 'quit']:
                print("Shutting down AOS...")
                self.running = False
                break

            if not user_input.strip():
                continue

            self.context_manager.append_l1(f"User: {user_input}")
            current_prompt = user_input

            # ReAct Loop: Allow kernel to process OS feedback up to 3 times before halting
            for step in range(3):
                print("--- Parsing Intent via Speculative Latent Kernel ---")
                context_string = "\n".join(self.context_manager.active_context[-5:])
                intents = self.inference_engine.parse_intent(current_prompt, context_history=context_string)

                if not intents:
                    print("No executable intent recognized.")
                    break

                terminal_reached = False
                os_feedback = []

                for intent in intents:
                    self.context_manager.add_intent(150)
                    thought = intent.get("thought_process", "Direct execution.")
                    print(f"[Latent Kernel Thought]: {thought}")

                    intent_type = intent.get("type")
                    payload = intent.get("payload", {})

                    # Execute mapped OS API calls
                    result = self.agent.execute_intent(intent_type, payload)

                    # Log inner monologue and OS response into L1 working memory
                    self.context_manager.append_l1(f"Kernel Reasoned: {thought} | OS Executed: {intent_type} with result: {result}")

                    if intent_type in ["NOTIFY_USER", "ASK_USER_INPUT"]:
                        terminal_reached = True
                    else:
                        os_feedback.append(f"{intent_type} returned: {result}")

                if terminal_reached or not os_feedback:
                    break

                # Auto-Callback trigger: feed results back to the kernel for multi-turn reasoning
                current_prompt = f"[System Callback]: {os_feedback}. Based on this, what is the next intent? (Use NOTIFY_USER or ASK_USER_INPUT if finished)"
                print(f"--- Triggering Auto-Callback: {os_feedback} ---")

            if getattr(self.agent, "virtual_os", None):
                print("\n[Virtual OS State Updated]")
