from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import socket
import json
import time
import math
import asyncio
import psutil
from typing import List
import threading

HOST = "0.0.0.0"
TCP_PORT = 8001
WS_PORT = 8000

app = FastAPI()
active_connections: List[WebSocket] = []

"""
@app.websocket("/ws/datos")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
"""
async def broadcast_data(data):
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except:
                 active_connections.remove(connection)
            
           
def get_resource_usage():
    process = psutil.Process()
    process.cpu_percent(interval=None)
    time.sleep(0.1)
    cpu_percent = process.cpu_percent(interval=None)
    cpu_percent_total = psutil.cpu_percent(interval=None)
    mem_info = process.memory_info()
    ram_mb = mem_info.rss / (1024 * 1024)
    ram_percent_total = psutil.virtual_memory().percent

    return {
        "cpu_process_percent": round(cpu_percent, 2),
        "cpu_equipo_total": round(cpu_percent_total, 2),
        "ram_process_mb": round(ram_mb, 2),
        "ram_equipo_total": round(ram_percent_total, 2),
    }

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


def start_tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, TCP_PORT))
        server.listen()
        print(f"Servidor TCP escuchando en {HOST}:{TCP_PORT}")

        conn, addr = server.accept()
        with conn:
            print(f"Conexión establecida con {addr}")

            hz = 100
            ts = 1 / hz
            duration_seconds = 100
            start_time = time.time()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            cantidad_paquetes = 0
            
            vscode_ram = get_ram_usage_by_name("Code.exe")
            
            cmd_ram = get_ram_usage_by_name("cmd.exe")
            
            prev_timestamp = None
            
            amplitud = 30
 
            while (time.time() - start_time) < duration_seconds:
                current_time = time.time() - start_time
                cantidad_paquetes += 1
                
                #y = amplitud * math.sin(2 * math.pi * hz * current_time)
                
                
                y = amplitud * math.sin(hz * current_time * 2 * math.pi)
                
                recursos = get_resource_usage()
                current_timestamp = time.time()

                delta_t = current_timestamp - prev_timestamp if prev_timestamp else None
                prev_timestamp = current_timestamp

                data = {
                    "cantidad_paquetes": cantidad_paquetes,
                    "tiempo_transcurrido": round(current_time, 2),
                    "hz": hz,
                    "ts": ts,
                    "cpu_process_percent": recursos["cpu_process_percent"],
                    "cpu_equipo_total": recursos["cpu_equipo_total"],
                    "ram_process_mb": recursos["ram_process_mb"],
                    "ram_equipo_total": recursos["ram_equipo_total"],
                    "x": round(current_time, 2),
                    "y": round(y, 4),
                    "ts_server": time.time(),
                    "vs_code_ram": vscode_ram,
                    "cmd_ram": cmd_ram,
                    "delta_t": round(delta_t, 6) if delta_t else None,
                }

                mensaje = json.dumps(data) + "\n"
                conn.sendall(mensaje.encode("utf-8"))
                loop.run_until_complete(broadcast_data(data))
                time.sleep(ts)
                
                
                """
                Quiero que pueda recebir datos de amplitud
                """
            recursos_finales = get_resource_usage()
            final_data = {
                "fin": True,
                "cantidad_paquetes": cantidad_paquetes,
                "hz": hz,
                "ts": ts,
                "tiempo_transcurrido": round(time.time() - start_time, 2),
                "cpu_process_percent": recursos_finales["cpu_process_percent"],
                "cpu_equipo_total": recursos_finales["cpu_equipo_total"],
                "ram_process_mb": recursos_finales["ram_process_mb"],
                "ram_equipo_total": recursos_finales["ram_equipo_total"],
                "ts_server": time.time(),
                "tiempo": duration_seconds,
                "vs_code_ram": vscode_ram,
                
                "x": round(current_time, 2),
                "y": round(y, 4),
                
                "cmd_ram": cmd_ram,
                "delta_t": round(delta_t, 6) if delta_t else None,
            }

            conn.sendall((json.dumps(final_data) + "\n").encode("utf-8"))
            loop.run_until_complete(broadcast_data(final_data))
            print("Transmisión finalizada")


if __name__ == "__main__":
    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=WS_PORT)
