# tcp_server_tiempo.py

import socket
import json
import time
import math
import asyncio
import psutil
import threading
from fastapi import FastAPI, WebSocket
from typing import List

# ===================== #
#      CONFIG GLOBAL    #
# ===================== #
HOST = "0.0.0.0"
TCP_PORT = 8001
WS_PORT = 8000
BUFFER_SIZE = 1024

app = FastAPI()
active_connections: List[WebSocket] = []

# ===================== #
#  FUNCIONES AUXILIARES #
# ===================== #

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

async def broadcast_data(data):
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except:
            active_connections.remove(connection)

# ========================== #
#     CLASE: TCPHandler      #
# ========================== #

class TCPHandler:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.params = {"amplitud": 30.0, "hz": 100.0, "segundos": 0, "stop": False}
        self.lock = threading.Lock()

    def receive_initial_config(self):
        buffer = ""
        try:
            while not buffer.endswith("\n"):
                buffer += self.conn.recv(BUFFER_SIZE).decode("utf-8")
            config = json.loads(buffer.strip())

            with self.lock:
                self.params["amplitud"] = float(config.get("amplitud", self.params["amplitud"]))
                self.params["hz"] = float(config.get("hz", self.params["hz"]))
                self.params["segundos"] = float(config.get("segundos", self.params["segundos"]))

        except Exception as e:
            print(f"[SERVER] Error leyendo configuración inicial: {e}")
            self.conn.close()
            return False
        return True

    def listen_for_updates(self):
        buffer = ""
        while not self.params["stop"]:
            try:
                data = self.conn.recv(BUFFER_SIZE)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    msg = json.loads(linea.strip())
                    with self.lock:
                        self.params["amplitud"] = float(msg.get("amplitud", self.params["amplitud"]))
                        self.params["hz"] = float(msg.get("hz", self.params["hz"]))
                        self.params["segundos"] = float(msg.get("segundos", self.params["segundos"]))
                        if msg.get("stop"):
                            self.params["stop"] = True
            except Exception as e:
                print(f"[SERVER] Error recibiendo parámetros: {e}")
                break

    def stream_signal(self):
        cantidad_paquetes = 0
        count_ts = 0
        start_time = time.time()
        prev_timestamp = None
        vscode_ram = get_ram_usage_by_name("Code.exe")
        cmd_ram = get_ram_usage_by_name("cmd.exe")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            while not self.params["stop"]:
                with self.lock:
                    ts = 1 / self.params["hz"]
                    amplitud = self.params["amplitud"]
                    duracion = self.params["segundos"]

                current_time = time.time() - start_time
                count_ts = round(count_ts + ts, 2)

                if duracion > 0 and current_time > duracion:
                    time.sleep(0.1)
                    continue

                y = amplitud * math.sin(2 * math.pi * count_ts + 4)
                recursos = get_resource_usage()
                cantidad_paquetes += 1

                timestamp_now = time.time()
                delta_t = timestamp_now - prev_timestamp if prev_timestamp else None
                prev_timestamp = timestamp_now

                data = {
                    "cantidad_paquetes": cantidad_paquetes,
                    "tiempo_transcurrido": round(current_time, 2),
                    "hz": self.params["hz"],
                    "ts": ts,
                    "x": round(current_time, 2),
                    "y": round(y, 2),
                    "ts_server": timestamp_now,
                    "delta_t": round(delta_t, 6) if delta_t else None,
                    **recursos,
                    "vs_code_ram": vscode_ram,
                    "cmd_ram": cmd_ram,
                }

                mensaje = json.dumps(data) + "\n"
                self.conn.sendall(mensaje.encode("utf-8"))
                loop.run_until_complete(broadcast_data(data))
                time.sleep(ts)

        except Exception as e:
            print(f"[SERVER] Error durante transmisión: {e}")
        finally:
            print(f"[SERVER] Conexión finalizada con {self.addr}")
            self.conn.close()

    def handle(self):
        print(f"[SERVER] Nueva conexión desde {self.addr}")
        if self.receive_initial_config():
            threading.Thread(target=self.listen_for_updates, daemon=True).start()
            self.stream_signal()

# ========================== #
#     CLASE: TCPServer       #
# ========================== #

class TCPServer:
    def __init__(self, host=HOST, port=TCP_PORT):
        self.host = host
        self.port = port

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            server.listen()
            print(f"[SERVER] TCP escuchando en {self.host}:{self.port}")

            while True:
                conn, addr = server.accept()
                handler = TCPHandler(conn, addr)
                threading.Thread(target=handler.handle, daemon=True).start()

# =========================== #
#       MAIN: Run server      #
# =========================== #

if __name__ == "__main__":
    tcp_server = TCPServer()
    tcp_thread = threading.Thread(target=tcp_server.start, daemon=True)
    tcp_thread.start()

    import uvicorn
    uvicorn.run(app, host=HOST, port=WS_PORT)
