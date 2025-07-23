import time
import asyncio
import httpx
import requests
from pathlib import Path
from pyrogram import Client
from pyrogram.types import Message
import mediafire_dl

from config import TELEGRAM_MAX_CHUNK_SIZE, DOWNLOAD_DIR, LOGGER
from helpers import split_file, progress_callback
from database import log_usage
from handlers import DOWNLOAD_QUEUE, ACTIVE_TASKS

async def process_mediafire_link(client: Client, message: Message):
    """Lógica principal para procesar enlaces de MediaFire y subir a Telegram."""
    user_id = message.from_user.id
    url = message.text
    status = await message.reply("🔍 Procesando tu enlace...", quote=True)

    file_path, parts = None, []
    try:
        await status.edit("⏬ Obteniendo enlace directo...")
        direct_url = await asyncio.to_thread(mediafire_dl.get_direct_download_link, url)
        filename = requests.utils.unquote(Path(direct_url).name)
        file_path = DOWNLOAD_DIR / filename

        start = time.time()
        size = 0
        state = {}

        async with httpx.AsyncClient(timeout=None) as client_http:
            async with client_http.stream("GET", direct_url) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                with file_path.open("wb") as f:
                    async for chunk in r.aiter_bytes(8192):
                        f.write(chunk)
                        size += len(chunk)
                        if total > 0:
                            await progress_callback(size, total, status, "Descargando", start, state)

        parts = await asyncio.to_thread(split_file, file_path, TELEGRAM_MAX_CHUNK_SIZE)

        for i, part in enumerate(parts):
            caption = f"{part.name}"
            if len(parts) > 1:
                caption += f" (Parte {i+1}/{len(parts)})"

            start_up = time.time()
            state_up = {}
            await client.send_document(
                chat_id=message.chat.id,
                document=str(part),
                caption=caption,
                progress=progress_callback,
                progress_args=(status, f"Subiendo Parte {i+1}/{len(parts)}", start_up, state_up)
            )

        await status.delete()
        await log_usage(user_id)

    except asyncio.CancelledError:
        LOGGER.info(f"Tarea cancelada por el usuario {user_id}")
        await status.edit("❌ Tarea cancelada.")
    except Exception as e:
        LOGGER.error(f"Error procesando {url}: {e}", exc_info=True)
        await status.edit(f"❌ Error inesperado.\n{e}")
    finally:
        for p in parts:
            if p.exists():
                p.unlink()
        if file_path and file_path.exists():
            file_path.unlink()

async def download_worker(name: str, client: Client):
    """Worker que atiende tareas en la cola de descargas."""
    LOGGER.info(f"⚙️ Worker {name} iniciado.")
    while True:
        try:
            message = await DOWNLOAD_QUEUE.get()
            user_id = message.from_user.id

            task = asyncio.create_task(process_mediafire_link(client, message))
            ACTIVE_TASKS[user_id] = task
            try:
                await task
            finally:
                ACTIVE_TASKS.pop(user_id, None)
                DOWNLOAD_QUEUE.task_done()
        except Exception as e:
            LOGGER.error(f"Error en worker {name}: {e}", exc_info=True)