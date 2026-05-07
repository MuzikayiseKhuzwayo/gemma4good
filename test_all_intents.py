import asyncio
from dotenv import load_dotenv

load_dotenv()

from aos_kernel.daemon import AOSDaemon
from aos_kernel.inference import GemmaLatentKernel
from shell_agent.api_mapper import ShellAgent
from semantic_fs.vector_store import SemanticFileSystem

async def test_all_paths():
    print("Testing All Abstract Intents...\n")
    
    sfs = SemanticFileSystem()
    agent = ShellAgent(use_virtual_env=True)
    kernel = AOSDaemon(fs=sfs, agent=agent)
    inference_engine = GemmaLatentKernel(mode="google_genai")
    
    test_prompts = [
        "Write a file at /test/data.txt with the content 'Hello World'.",
        "Read the file at /test/data.txt.",
        "Delete the file at /test/data.txt.",
        "Search memory for 'vacation plans'.",
        "Send a message to John with the body 'Meeting at 5'.",
        "Notify me that the system is shutting down.",
        "I need more context. Ask me what my favorite color is."
    ]
    
    for prompt in test_prompts:
        print(f"\n--- Testing Intent extraction for Prompt: '{prompt}' ---")
        intents = inference_engine.parse_intent(prompt)
        print("Extracted Intents:", intents)
        
        if not intents:
            print("Failed to extract intents!")
            await asyncio.sleep(2)
            continue
            
        print("Executing Intents in Virtual OS:")
        for intent in intents:
            intent_type = intent.get("type")
            payload = intent.get("payload", {})
            try:
                result = agent.execute_intent(intent_type, payload)
                print(f"Result for {intent_type}: {result}")
            except Exception as e:
                print(f"Error executing {intent_type}: {e}")
        
        # Prevent rate limits
        await asyncio.sleep(2)
                
    print("\n--- Final Virtual OS State ---")
    state = agent.virtual_os.get_state_summary()
    for key, value in state.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(test_all_paths())
