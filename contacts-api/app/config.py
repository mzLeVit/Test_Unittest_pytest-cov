from pydantic_settings import BaseSettings
import os
import sys

sys.path.insert(0, os.path.abspath('../'))


class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]

settings = Settings()
