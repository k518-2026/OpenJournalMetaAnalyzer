"""Configuration settings for OpenJournalMetaAnalyzer."""
import os
from pydantic import BaseModel

class AppConfig(BaseModel):
    APP_NAME: str = "OpenJournalMetaAnalyzer"
    APP_VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API Endpoints
    OPENALEX_API_URL: str = "https://api.openalex.org/works"
    EUROPE_PMC_API_URL: str = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    # Default User-Agent (Polite pool for OpenAlex)
    USER_AGENT: str = "OpenJournalMetaAnalyzer/1.0 (mailto:academic-researcher@example.org)"
    HTTP_TIMEOUT_SECONDS: float = 20.0
    
    # Optional Gemini LLM Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

config = AppConfig()
