import os
import logging
import threading
import time
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Configuración de logging
title = os.getenv("JOB_NAME", "mediafire_bot")
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(title)

# Variables de entorno
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# Funciones de utilidad
def get_direct_link(mediafire_url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(mediafire_url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    btn = soup.find("a", {"id": "downloadButton"})
    return btn["href"] if btn else None

def download_file(url: str, dest: str, progress_key: dict):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    with open(dest, 'wb') as f:
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=1024*50):
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            progress_key['downloaded'] = downloaded
            progress_key['total'] = total
    return dest

async def send_status(bot: Bot, chat_id: int, progress_key: dict, stage: str):
    pct = int(progress_key['downloaded'] / progress_key['total'] * 100) if progress_key['total'] else 0
    await bot.send_message(chat_id, f"{stage}: {pct}%")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('¡Hola! Envía un enlace de Mediafire y te devolveré el archivo.')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/start - Inicio\n/help - Ayuda')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if 'mediafire.com' not in url:
        return await update.message.reply_text('Por favor, envía un enlace válido de Mediafire.')

    chat_id = update.message.chat_id
    key = {'downloaded': 0, 'total': 0}

    await update.message.reply_text('Obteniendo enlace directo...')
    dl_link = get_direct_link(url)
    if not dl_link:
        return await update.message.reply_text('No pude extraer el enlace. Intenta más tarde.')

    local_path = f"/tmp/{int(time.time())}_file"
    def thread_download():
        download_file(dl_link, local_path, key)
    threading.Thread(target=thread_download).start()

    for _ in range(60):
        await send_status(context.bot, chat_id, key, 'Descargando')
        if key['downloaded'] >= key['total']:
            break
        time.sleep(5)

    await update.message.reply_text('Subiendo archivo...')
    await context.bot.send_document(chat_id, open(local_path, 'rb'))
    os.remove(local_path)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

if __name__ == '__main__':
    if not TOKEN:
        logger.error('No se encontró TELEGRAM_BOT_TOKEN en variables de entorno')
        exit(1)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    app.run_polling()
