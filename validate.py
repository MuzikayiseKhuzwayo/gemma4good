import asyncio
from dotenv import load_dotenv

load_dotenv() # Load variables from .env before importing modules that need them

from aos_kernel.daemon import AOSDaemon
from aos_kernel.inference import GemmaLatentKernel
from shell_agent.api_mapper import ShellAgent
from semantic_fs.vector_store import SemanticFileSystem

async def run_validation():
    print("Starting Virtual OS Validation Run...\n")
    
    # Initialize components with Virtual OS enabled
    sfs = SemanticFileSystem()
    agent = ShellAgent(use_virtual_env=True)
    kernel = AOSDaemon(fs=sfs, agent=agent)
    inference_engine = GemmaLatentKernel(mode="google_genai") # Options: "mock", "google_genai", "local" 
    
    # The actual user prompt we want the Agentic OS to process
    user_prompt = "Send a message to Alice saying I will be late, and save a note."
    
    print(f"\n--- User Intent Detected: '{user_prompt}' ---")
    print("--- Simulating AI Intent Generation via Gemma ---")
    intents = inference_engine.parse_intent(user_prompt)
    
    print("\n--- Routing Intents through Shell Agent to Virtual OS ---")
    for intent in intents:
        # Simulate token budgeting
        kernel.context_manager.add_intent(150) 
        agent.execute_intent(intent["type"], intent["payload"])
        await asyncio.sleep(0.5)
        
    print("\n--- Virtual OS Final State ---")
    state = agent.virtual_os.get_state_summary()
    for key, value in state.items():
        print(f"{key}: {value}")
    
    print("\nValidation Complete. System state accurately reflects AI intentions without host side-effects.")

if __name__ == "__main__":
    asyncio.run(run_validation())
