import os
import logging
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from telegram import Bot

# Config
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
bot = Bot(token=TOKEN)
WEBHOOK_PATH = f"/webhook/{TOKEN}"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mediafire_bot_webhook")

app = FastAPI()

class UpdateModel(BaseModel):
    update_id: int
    message: dict = None

def get_direct_link(mediafire_url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(mediafire_url, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    btn = soup.find("a", {"id": "downloadButton"})
    return btn["href"] if btn else None

def download_and_send(chat_id: int, url: str):
    try:
        direct = get_direct_link(url)
        if not direct:
            bot.send_message(chat_id, "No pude extraer el enlace. Intenta más tarde.")
            return
        bot.send_message(chat_id, "Descargando archivo...")
        r = requests.get(direct, stream=True)
        # Send document by streaming chunks
        bot.send_document(chat_id, r.raw)
    except Exception as e:
        logger.error("Error en descarga/envío: %s", e)
        bot.send_message(chat_id, f"Error: {e}")

@app.post(WEBHOOK_PATH)
async def telegram_webhook(update: UpdateModel, request: Request):
    if update.message and "text" in update.message:
        text = update.message["text"].strip()
        chat_id = update.message["chat"]["id"]
        if text in ["/start", "/help"]:
            await app.router.call_route_function(
                request=request,
                func=lambda: bot.send_message(chat_id, "Envía un enlace de Mediafire para descargar.")
            )
        elif "mediafire.com" in text:
            # Process download
            download_and_send(chat_id, text)
        else:
            bot.send_message(chat_id, "Por favor, envía un enlace válido de Mediafire.")
    return {"ok": True}

@app.on_event("startup")
async def startup():
    # Set webhook
    domain = os.getenv("APP_URL")
    if not domain:
        raise RuntimeError("APP_URL not set")
    url = f"{domain}{WEBHOOK_PATH}"
    bot.set_webhook(url)
    logger.info("Webhook establecido en %s", url)
