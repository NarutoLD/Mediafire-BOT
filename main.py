import os
import logging
from fastapi import FastAPI
import uvicorn
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mediafire_web_bot")

# Instancia del bot
bot = Client("mediafire_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Crear app FastAPI
app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("Iniciando bot de Telegram...")
    await bot.start()
    logger.info("✅ Bot iniciado correctamente.")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Deteniendo bot de Telegram...")
    await bot.stop()
    logger.info("🛑 Bot detenido.")

@app.get("/")
def root():
    return {"status": "✅ El bot está funcionando correctamente."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
