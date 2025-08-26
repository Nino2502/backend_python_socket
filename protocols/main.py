from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import math
import time
import psutil
app = FastAPI()
# Middleware para permitir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_ram_usage_by_name(target_name: str):
    total_ram = 0.0
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            if proc.info['name'] and target_name.lower() in proc.info['name'].lower():
                ram_mb = proc.info['memory_info'].rss / (1024 * 1024)
                total_ram += ram_mb
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return round(total_ram, 2) if total_ram > 0 else None

@app.get("/http/sine/{index}")
def get_sine_paquete(index: int):
    process = psutil.Process()
    process.cpu_percent(interval=None)
    time.sleep(0.1) 
    cpu_percent = process.cpu_percent(interval=None)
    cpu_percent_total = psutil.cpu_percent(interval=None)
    hz = 100
    ts = 1 / hz
    y = math.sin(index * ts * 2 * math.pi)
    ts_server = time.time()
    mem_info = process.memory_info()
    ram_mb = mem_info.rss / (1024 * 1024)
    ram_percent_total = psutil.virtual_memory().percent

    return JSONResponse(content={
        "x": index,
        "y": round(y, 4),
        "ts_server": ts_server,
        "ts": ts,
        "hz": hz,
        "cpu_percent": cpu_percent,
        "cpu_equipo_total": cpu_percent_total,
        "ram_mb": round(ram_mb, 2),
        "ram_equipo_total": ram_percent_total
    })


