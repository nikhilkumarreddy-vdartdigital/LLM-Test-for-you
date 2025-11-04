from browser_use import ChatGoogle, Agent
from langchain_google_genai import ChatGoogleGenerativeAI


from settings import settings

llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GOOGLE_API_KEY,
    temperature=0.0
)

browser_use_llm = ChatGoogle(
    model="gemini-flash-latest",
    temperature=0.0,
    api_key=settings.GOOGLE_API_KEY

)

async def perform_browser_task(task) -> str:
    agent = Agent(task=task, llm=browser_use_llm)
    result = await agent.run()
    return result


if __name__ == '__main__':
    base_url = "https://www.saucedemo.com/"





