from typing import Optional, Dict

import instructor
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Browser, Agent, ChatGoogle, BrowserProfile
import asyncio
import sys

from settings import settings


langchain_google_llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0
)

instructor_patched_google_llm_client = instructor.from_provider(
    "google/" + settings.GEMINI_MODEL,
    api_key=settings.GOOGLE_API_KEY,
    async_client=True
)

browser_use_google_llm = ChatGoogle(
    model=settings.GEMINI_MODEL,
    api_key=settings.GOOGLE_API_KEY,
    temperature=0.0
)



STREAMLIT_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-success {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .status-error {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .status-info {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
"""

def run_coro(coro):
    """
    Run an async coroutine from synchronous code safely.
    Uses asyncio.run where possible, falls back to creating a temporary event loop
    and performs shutdown of async generators to avoid unclosed transport warnings.
    """
    # Set the event loop policy for Windows compatibility
    import platform
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        current_loop = asyncio.get_event_loop() or asyncio.ProactorEventLoop()
        asyncio.set_event_loop(current_loop)
    except RuntimeError:
        current_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(current_loop)
    try:
        return current_loop.run_until_complete(coro)
    finally:
        # Properly shutdown async generators to avoid warnings
        current_loop.run_until_complete(current_loop.shutdown_asyncgens())
        # Close the loop if it was newly created
        if not asyncio.get_event_loop().is_running():
            current_loop.close()