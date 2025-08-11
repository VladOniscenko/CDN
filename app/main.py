from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import urllib.parse
import imghdr
import os
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

from . import storage
from .storage import make_dir

load_dotenv()

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

ALLOWED_CONTENT_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
}

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf'}


class AllowedHostsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0]
        if ALLOWED_HOSTS and host not in ALLOWED_HOSTS:
            raise HTTPException(status_code=403, detail="Host not allowed")
        return await call_next(request)


def allowed_file(filename: str, content_type: str, file_bytes: bytes) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS or content_type not in ALLOWED_CONTENT_TYPES:
        return False

    if content_type.startswith('image/'):
        kind = imghdr.what(None, h=file_bytes)
        if kind is None:
            return False
        # Zorg dat extensie overeenkomt met het gedetecteerde type
        if ext in ['.jpg', '.jpeg'] and kind != 'jpeg':
            return False
        if ext == '.png' and kind != 'png':
            return False
        if ext == '.gif' and kind != 'gif':
            return False
    return True


app = FastAPI(title="Simple CDN")
app.add_middleware(AllowedHostsMiddleware)

app.mount('/cdn', StaticFiles(directory=storage.BASE_DIR), name='cdn')

templates = Jinja2Templates(directory=Path(__file__).parent.joinpath('templates'))


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    dirs, files = storage.list_dir('')
    return templates.TemplateResponse('browse.html', {'request': request, 'current': '', 'dirs': dirs, 'files': files})


@app.get('/browse/{path:path}', response_class=HTMLResponse)
async def browse(request: Request, path: str):
    dirs, files = storage.list_dir(path)
    return templates.TemplateResponse('browse.html', {'request': request, 'current': path, 'dirs': dirs, 'files': files})


@app.post('/upload')
async def upload(file: UploadFile = File(...), dir: str = Form('')):
    if '..' in dir:
        raise HTTPException(status_code=400, detail='invalid dir')

    content = await file.read()
    if not allowed_file(file.filename, file.content_type, content):
        raise HTTPException(status_code=400, detail='Invalid file type')

    saved = storage.save_file(dir, file.filename, content)

    url = f"/cdn/{urllib.parse.quote(saved)}"
    return {'status': 'ok', 'path': saved, 'url': url}


@app.post("/mkdir")
async def mkdir(base_dir: str = Form(""), new_dir: str = Form(...)):
    full_path = os.path.join(base_dir, new_dir).strip("/")
    make_dir(full_path)
    return RedirectResponse(url=f"/browse/{base_dir}", status_code=303)


@app.post('/delete')
async def remove(path: str = Form(...)):
    if '..' in path:
        raise HTTPException(status_code=400, detail='invalid path')
    ok = storage.delete_path(path)
    if not ok:
        raise HTTPException(status_code=400, detail='not empty or not found')
    parent_dir = path.rsplit('/', 1)[0]
    return RedirectResponse(url=f"/browse/{parent_dir}", status_code=303)


@app.get('/download/{path:path}')
async def download(path: str):
    p = storage.safe_join(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(p, filename=p.name)
