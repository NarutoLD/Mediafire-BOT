import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, DOWNLOAD_DIR, MAX_CONCURRENT_DOWNLOADS, LOGGER
from database import db_init
from workers import download_worker
from handlers import register_handlers

app = Client("mediafire_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def main():
    LOGGER.info("📁 Creando directorio de descargas...")
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    LOGGER.info("🗄️ Inicializando base de datos...")
    await db_init()

    LOGGER.info("🤖 Iniciando cliente Pyrogram...")
    await app.start()
    me = await app.get_me()
    LOGGER.info(f"✅ Bot iniciado como @{me.username}")

    register_handlers(app)

    LOGGER.info(f"🚚 Iniciando {MAX_CONCURRENT_DOWNLOADS} workers...")
    workers = [
        asyncio.create_task(download_worker(f"worker-{i}", app))
        for i in range(MAX_CONCURRENT_DOWNLOADS)
    ]

    await asyncio.Event().wait()

    for w in workers:
        w.cancel()
    await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info("❌ Bot detenido manualmente.")