import os
import logging
from pathlib import Path

# Logging global
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger("mediafire_bot")

# Variables de entorno
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))

# Validación
if not all([API_ID, API_HASH, BOT_TOKEN, ADMIN_USER_ID]):
    LOGGER.critical("❌ Faltan variables de entorno.")
    exit(1)

# Rutas y tamaños
BASE_DIR = Path.cwd()
DOWNLOAD_DIR = BASE_DIR / "downloads"
DB_PATH = BASE_DIR / "bot_auth.db"
TELEGRAM_MAX_CHUNK_SIZE = 1998 * 1024 * 1024  # 1.99 GB