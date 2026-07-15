import asyncio
from google.antigravity import Agent, LocalAgentConfig

async def test_agent():
    config = LocalAgentConfig()
    async with Agent(config) as agent:
        resp = await agent.chat("What is the current version of python you are running in? Use python code to check if possible.")
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(test_agent())
