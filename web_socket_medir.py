import math
import asyncio
import time
import psutil
from fastapi import FastAPI, WebSocket

app = FastAPI()

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


@app.websocket("/ws/socket_web")
async def websocket_ruta(websocket: WebSocket):
    await websocket.accept()
    hz = 100
    ts = 1 / hz
    i = 0
    duracion = 120
    t0 = time.time()
    process = psutil.Process()  
    process.cpu_percent(interval=0.1) 
    while time.time() - t0 < duracion:
        y = math.sin(ts * i * 2 * math.pi)
        cpu_percent = process.cpu_percent(interval=None)
        cpu_percent_total = psutil.cpu_percent(interval=None)
        mem_info = process.memory_info()
        ram_mb = mem_info.rss / (1024 * 1024)
        ram_percent_total = psutil.virtual_memory().percent
        vscode_ram = get_ram_usage_by_name("Code.exe")
        cmd_ram = get_ram_usage_by_name("cmd.exe")
        await websocket.send_json({
            "cantidad_paquetes": i,
            "x": round(i, 2),
            "y": round(y, 4),
            "hz": hz,
            "x_paquetes": ts,
            "ts_server": time.time(),
            "cpu_percent": cpu_percent,
            "cpu_equipo_total" : cpu_percent_total,
            "ram_mb": round(ram_mb, 2),
            "ram_equipo_total" : ram_percent_total,
            "duracion": duracion,
            "vs_code_ram": vscode_ram,
            "cmd_ram": cmd_ram
        })
        i += 1
        await asyncio.sleep(ts)
    await websocket.send_json({
        "fin": True,
        "cantidad_paquetes": i,
        "hz": hz,
        "x_paquetes": ts,
        "ts_server": time.time(),
        "cpu_percent": process.cpu_percent(interval=None),
        "ram_mb": round(process.memory_info().rss / (1024 * 1024), 2),
        "duracion": duracion,
        "vs_code_ram": vscode_ram,
        "cmd_ram": cmd_ram
    })   
    #uvicorn web_socket_medir:app --reload
