"""
Configuración central del servicio independiente de IA Marketing.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Local Flask and AI development share the backend environment file. Docker
# supplies these values directly through the container environment.
load_dotenv()
load_dotenv(BASE_DIR.parent / "backend" / ".env", override=False)

# Los datasets se mantienen en una sola ubicación. Docker puede reemplazarla con DATA_DIR.
DEFAULT_DATA_DIR = BASE_DIR.parent / "backend" / "data" / "market"

class Settings:
    PORT: int = int(os.getenv("AI_SERVICE_PORT", "5001"))
    HOST: str = os.getenv("AI_SERVICE_HOST", "0.0.0.0")
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY") or os.getenv("AI_INTERNAL_API_KEY", "")
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR)))

    # Proveedores de LLM opcionales
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openai").lower()
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")

settings = Settings()
