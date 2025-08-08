# file_server.py

import os
import io
import zipfile
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
import json
import MetaTrader5 as mt5

# ===== KONFIGURACJA TOKENU =====
ACCESS_TOKEN = "TwojSuperSekretnyToken123456"  # <- zmień na swój!

# ===== DANE LOGOWANIA MT5 (pobierz z pliku JSON) =====
def load_mt5_secrets(config_path="data_providers/mt5_secrets.json"):
    if not os.path.exists(config_path):
        raise RuntimeError(f"Brak pliku konfiguracyjnego: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

secrets = load_mt5_secrets()
MT5_LOGIN = int(secrets["MT5_LOGIN"])
MT5_PASSWORD = secrets["MT5_PASSWORD"]
MT5_SERVER = secrets["MT5_SERVER"]
MT5_PATH = secrets.get("MT5_PATH", None)
MT5_SYMBOL = secrets.get("MT5_SYMBOL", "EURUSD")

# ===== TWORZENIE APP FASTAPI =====
app = FastAPI()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ===== AUTORYZACJA PRZEZ TOKEN =====
def authorize(authorization: str):
    if authorization != f"Bearer {ACCESS_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

# ===== INICJALIZACJA MT5 =====
@app.on_event("startup")
def mt5_connect():
    if MT5_PATH:
        mt5.initialize(MT5_PATH)
    else:
        mt5.initialize()
    authorized = mt5.login(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        raise RuntimeError(f"MT5 login failed: {mt5.last_error()}")

@app.on_event("shutdown")
def mt5_shutdown():
    mt5.shutdown()

# ===== LISTING KATALOGÓW =====
@app.get("/list/")
def list_dir(path: str = "", authorization: str = Header(None)):
    authorize(authorization)
    target = os.path.abspath(os.path.join(BASE_DIR, path))
    if not target.startswith(BASE_DIR):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Directory not found")
    entries = []
    for name in os.listdir(target):
        full = os.path.join(target, name)
        entries.append({
            "name": name,
            "is_dir": os.path.isdir(full),
            "size": os.path.getsize(full) if os.path.isfile(full) else None
        })
    return {"path": path, "entries": entries}

# ===== POBIERANIE PLIKU =====
@app.get("/download/")
def download_file(path: str, authorization: str = Header(None)):
    authorize(authorization)
    target = os.path.abspath(os.path.join(BASE_DIR, path))
    if not target.startswith(BASE_DIR) or not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target, filename=os.path.basename(target))

# ===== POBIERANIE ZIP KATALOGU =====
@app.get("/download_zip/")
def download_zip(path: str, authorization: str = Header(None)):
    authorize(authorization)
    target = os.path.abspath(os.path.join(BASE_DIR, path))
    if not target.startswith(BASE_DIR) or not os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Directory not found")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(target):
            for file in files:
                fp = os.path.join(root, file)
                z.write(fp, os.path.relpath(fp, target))
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{os.path.basename(target)}.zip"'})

# ===== INFORMACJE Z MT5 (np. saldo, lista instrumentów) =====
@app.get("/mt5/account/")
def mt5_account(authorization: str = Header(None)):
    authorize(authorization)
    info = mt5.account_info()._asdict()
    return JSONResponse(content=info)

@app.get("/mt5/symbols/")
def mt5_symbols(authorization: str = Header(None)):
    authorize(authorization)
    symbols = mt5.symbols_get()
    result = [s.name for s in symbols]
    return JSONResponse(content={"symbols": result})

# ===== LOGOWANIE KAŻDEJ AKCJI =====
import logging
logging.basicConfig(filename="file_server.log", level=logging.INFO, format="%(asctime)s %(message)s")

@app.middleware("http")
async def log_requests(request, call_next):
    logging.info(f"{request.method} {request.url} HEADERS={dict(request.headers)}")
    response = await call_next(request)
    return response

# ===== STRONA POWITALNA =====
@app.get("/")
def root():
    return {"msg": "GIE file server is alive. Use /list, /download, /download_zip, /mt5/account, /mt5/symbols endpoints."}
