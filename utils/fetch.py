# utils/fetch.py
import aiohttp
import os
from pathlib import Path
from urllib.parse import urlparse

async def download_file(url: str, dest_dir: str = "downloads") -> str:
    os.makedirs(dest_dir, exist_ok=True)
    parsed = urlparse(url)
    filename = Path(parsed.path).name or "downloaded"
    dest = Path(dest_dir) / filename
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Download failed: {resp.status} for {url}")
            data = await resp.read()
            dest.write_bytes(data)
    return str(dest)
