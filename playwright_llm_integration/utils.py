import threading
from concurrent.futures import ThreadPoolExecutor
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
import asyncio
import platform
from typing import Any

# ============================================================================
# ASYNC RUNNER - Handles async operations in a dedicated thread
# ============================================================================

class AsyncRunner:
    """
    Manages async operations in a dedicated thread with a persistent event loop.
    This prevents event loop conflicts in Streamlit's synchronous environment.
    """

    def __init__(self):
        self._loop = None
        self._thread = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._setup_loop()

    def _setup_loop(self):
        """Initialize event loop in a dedicated thread."""

        def run_loop():
            if platform.system() == "Windows":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

        # Wait for loop to be ready
        import time
        while self._loop is None:
            time.sleep(0.01)

    def run(self, coro):
        """Run a coroutine and return the result."""
        if self._loop is None or not self._loop.is_running():
            raise RuntimeError("Event loop is not running")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def cleanup(self):
        """Clean up the event loop and thread."""
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=5)
        self._executor.shutdown(wait=True)
