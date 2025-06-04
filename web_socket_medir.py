from fastapi import FastAPI, WebSocket
import math
import asyncio
import time
import psutil

app = FastAPI()

@app.websocket("/ws/socket_web")
async def websocket_ruta(websocket: WebSocket):
    await websocket.accept()
    hz = 10
    ts = 1 / hz
    i = 0
    duracion = 120
    t0 = time.time()
    process = psutil.Process()  
    
    
    
    process.cpu_percent(interval=0.1) 
    while time.time() - t0 < duracion:
        
        y = math.sin(ts * i * 2 * math.pi)
        
        
        #CPU PROCESO DE SCRIPT PYTHON
        cpu_percent = process.cpu_percent(interval=None)
        
        #CPU TOTAL DEL EQUIPO
        cpu_percent_total = psutil.cpu_percent(interval=None)
        
        
        mem_info = process.memory_info()
        
        
        #ram PROCESO DE SCRIPT PYTHON
        ram_mb = mem_info.rss / (1024 * 1024)
        
        #RAM TOTAL DEL EQUIPO
        ram_percent_total = psutil.virtual_memory().percent
        
        
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
            "duracion": duracion
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
        "duracion": duracion
    })

                
        #uvicorn web_socket_medir:app --reload
