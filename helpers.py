
---

## 4️⃣ `helpers.py`

```python
import math
import time
from pathlib import Path
from typing import List
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageNotModified
from config import LOGGER

def human_readable_size(size_bytes: int) -> str:
    if size_bytes == 0: return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

async def progress_callback(current, total, message: Message, action: str, start_time: float, state: dict):
    now = time.time()
    if (now - state.get("last_update", 0)) < 2: return
    state["last_update"] = now

    percentage = current * 100 / total
    speed = current / (now - start_time) if (now - start_time) > 0 else 0
    bar = "[" + "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10)) + "]"

    text = (
        f"{action}\n{bar} {percentage:.1f}%\n"
        f"{human_readable_size(current)} de {human_readable_size(total)}\n"
        f"Velocidad: {human_readable_size(speed)}/s"
    )

    try:
        await message.edit_text(text)
    except (MessageNotModified, FloodWait):
        pass
    except Exception as ex:
        LOGGER.warning(f"Error en barra de progreso: {ex}")

def split_file(file_path: Path, chunk_size: int) -> List[Path]:
    parts = []
    if not file_path.exists(): return parts
    if file_path.stat().st_size <= chunk_size: return [file_path]

    with file_path.open('rb') as f:
        part_num = 1
        while True:
            chunk = f.read(chunk_size)
            if not chunk: break
            part = file_path.with_suffix(f".part{part_num:03d}")
            part.write_bytes(chunk)
            parts.append(part)
            part_num += 1
    return parts