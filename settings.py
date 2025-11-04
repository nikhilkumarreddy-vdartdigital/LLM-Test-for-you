from pprint import pprint

from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    FIRE_CRAWL_API_KEY: str
    VECTOR_COLLECTION: str = ""

    model_config = ConfigDict(use_enum_values=True)


settings = Settings()

pprint(settings.model_dump())