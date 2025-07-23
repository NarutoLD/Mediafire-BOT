import logging
from pathlib import Path

# Logging global
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger("mediafire_bot")

# 🔧 Credenciales de Telegram
API_ID = 11639974
API_HASH = "a5007babf6f3e96c9b51564356b64c30"
BOT_TOKEN = "6055585696:AAFb_a1aqBuSF5YwrlIPI2iIrnV6QYauexo"
ADMIN_USER_ID = 882455317  # Tu ID de Telegram

MAX_CONCURRENT_DOWNLOADS = 2

# Validación
if not all([API_ID, API_HASH, BOT_TOKEN, ADMIN_USER_ID]):
    LOGGER.critical("❌ Faltan credenciales en config.py.")
    exit(1)

# Rutas y tamaños
BASE_DIR = Path.cwd()
DOWNLOAD_DIR = BASE_DIR / "downloads"
DB_PATH = BASE_DIR / "bot_auth.db"
TELEGRAM_MAX_CHUNK_SIZE = 1998 * 1024 * 1024  # 1.99 GB
