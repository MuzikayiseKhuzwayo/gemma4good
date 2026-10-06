import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import asyncio
from dotenv import load_dotenv

load_dotenv()

from aos_kernel.daemon import AOSDaemon
from shell_agent.api_mapper import ShellAgent
from semantic_fs.vector_store import SemanticFileSystem

async def main():
    print("Booting Agentic OS (AOS)...")
    
    # Initialize components
    sfs = SemanticFileSystem()
    agent = ShellAgent(use_virtual_env=True) # Run safely in virtual sandbox
    kernel = AOSDaemon(fs=sfs, agent=agent)
    
    print("AOS Kernel initialized.")
    await kernel.run()

if __name__ == "__main__":
    asyncio.run(main())
