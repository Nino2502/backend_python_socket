import socket
#sOCKET ES PARA crear y manejasr conexiones TCP
import json

import time

import math

import psutil

import threading

import signal

#threading ES PARA manejar múltiples conexiones simultáneas basicamentes HILOS YA SEA PARA ENVIAR O EDITAR TRAMAS DE INFORMACIÓN
# ================================ #
# Autor: Jesus Gonzalez Leal (Nino :3)
# Fecha: 24 de junio del 2025      #
# Ultima modificacion: 24 de nunio del 2025
# ================================ #

HOST = "0.0.0.0"
#eSTE ES LA IP DONDE EL SERVIDOR ESCUCHARÁ LAS CONEXIONES (tODAS LAS INTERFACES)
TCP_PORT = 8001
#Esto basicamente es el port donde el servidor TCP escuchará las conexiones entrantes
#Y ademas donde se mandar y se recibirá la información
BUFFER_SIZE = 1024
#BUFFER_SIZE ES EL TAMAÑO QUE SE PODRA ENVIAR Y RECIBIR EN CADA PETICIÓN LA INFORMACION
# ========================== #

def get_resource_usage():
    process = psutil.Process()
    process.cpu_percent(interval=None)
    time.sleep(0.1)
    cpu_percent = process.cpu_percent(interval=None)
    cpu_percent_total = psutil.cpu_percent(interval=None)
    mem_info = process.memory_info()
    ram_mb = mem_info.rss / (1024 * 1024)
    ram_percent_total = psutil.virtual_memory().percent
    
    nucleos_logicos = psutil.cpu_count(logical=True)
    
    nucleos_fisicos = psutil.cpu_count(logical=False)
    
    #print(f"Núcleos físicos: {nucleos_fisicos}")
    #print(f"Núcleos lógicos: {nucleos_logicos}")
    
    #Esta funcion obtiene el uso de recursos del sistema, incluyendo CPU y RAM.

    return {
        "cpu_process_percent": round(cpu_percent, 2),
        "cpu_equipo_total": round(cpu_percent_total, 2),
        "ram_process_mb": round(ram_mb, 2),
        "ram_equipo_total": round(ram_percent_total, 2),
        "nucleos_logicos" : nucleos_logicos,
        "nucleos_fisicos" : nucleos_fisicos
    }

    #Y despues basicamente lo retorno con un array lleno de objectos con los datos de uso de recursos
    #Psra acceder a los datos con la funcion de mandar datos por socket
    
""""
def get_ram_usage_by_name(target_name: str):
    #Esta funcion busca procesos que se estan cargando en segundos planos que contanga
    #tzarget_name en su nombre y retorna el uso de RAM en MB
    total_ram = 0.0
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            if proc.info['name'] and target_name.lower() in proc.info['name'].lower():
                ram_mb = proc.info['memory_info'].rss / (1024 * 1024)
                total_ram += ram_mb
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return round(total_ram, 2) if total_ram > 0 else None

"""

# ========================== #
#     CLASE: TCPHandler      #
# ========================== #

class TCPHandler:
    #Se encarga de manejar la conexión TCP con un cliente específico o 
    #Varios cleientes a la vez, recibiendo y enviando datos de forma concurrente.
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        #Guardamos la conexion TCP y la dirección del cliente
        self.params = {"amplitud": 30.0, "hz": 100.0, "stop": False, "segundos": 10.0}

        #Definimos los parámetros iniciales que se pueden modificar

        self.lock = threading.Lock()
        #Este es unlock que ayuda a proteger la lectura y la escritura de los parámetros (osea editar los parámetros)
        #Cuando se modifican desde múltiples hilos, evitando condiciones de carrera.

    def receive_initial_config(self):
        #En esta funcion se van a recbir los primero paramentos de configuración del cliente
        buffer = ""
        try:
            while not buffer.endswith("\n"):
                buffer += self.conn.recv(BUFFER_SIZE).decode("utf-8")
                
                print(f"[SERVER] Recibiendo configuración inicial: {buffer}")
                #Aqui todos los datos que se reciban del cliente se van a guardar en el buffer
                #Y los separamos por un salto de línea
            config = json.loads(buffer.strip())
            #En config todos los datos que se recibieron del cliente se van a guardar en un objeto JSON

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
            #Aqui validamos que no se mande el parametro ["stop"] Y para que no se detenga
            try:
                data = self.conn.recv(BUFFER_SIZE)
                #Escucha los parametros editados en tiempo real para que te puedas volver a mandar los datos
                if not data:
                    break
                buffer += data.decode("utf-8")
                #Aqui todos los datos los ponemos en formato UTF-8
                while "\n" in buffer:
                    #Aqui creamos un bucle que la variable buffer contenga saltos de línea
                    linea, buffer = buffer.split("\n", 1)
                    msg = json.loads(linea.strip())
                    with self.lock:
                        #Aqui se bloquea el acceso a los parámetros para evitar condiciones de carrera (osea de modulo que se edite al mismo tiempo)
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
        
        """"
        vscode_ram = get_ram_usage_by_name("Code.exe")
        cmd_ram = get_ram_usage_by_name("cmd.exe")
        
        """

        try:
            while not self.params["stop"]:
                with self.lock:
                    
                    ts = 1 / self.params["hz"]
                    
                    amplitud = self.params["amplitud"]
                    
                    hz = self.params["hz"]
                    
                    segundos =  self.params["segundos"]

                
                print(f"Soy datos de parametros {segundos} <<-- Segundos --> ts :  {ts} {amplitud} {hz}")
                
           

                current_time = time.time() - start_time
                count_ts = round(count_ts + ts, 4)  # mejor precisión para tiempo

                
                #y = amplitud * math.sin(2 * math.pi * self.params["hz"] * count_ts + 4)
                
                y = amplitud * math.sin(2 * math.pi * count_ts + 4)

                recursos = get_resource_usage()
                cantidad_paquetes += 1

                timestamp_now = time.time()
                delta_t = timestamp_now - prev_timestamp if prev_timestamp else None
                prev_timestamp = timestamp_now

                data = {
                    "cantidad_paquetes": cantidad_paquetes,
                    "tiempo_transcurrido": round(current_time, 4),
                    "hz": hz,
                    "ts": ts,
                    "segundos": segundos,
                    "x": round(current_time, 4),
                    "y": round(y, 4),
                    "ts_server": timestamp_now,
                    "delta_t": round(delta_t, 6) if delta_t else None,
                    **recursos
                }

                mensaje = json.dumps(data) + "\n"
                self.conn.sendall(mensaje.encode("utf-8"))
                time.sleep(ts)

        except Exception as e:
            print(f"[SERVER] Error durante transmisión: {e}")
        finally:
            print(f"[SERVER] Conexión finalizada con {self.addr}")
            self.conn.close()

    def handle(self):
        #Cuando el cliente se conecta al servidor entra a esta funcion
        print(f"[SERVER] Nueva conexión desde {self.addr}")
        if self.receive_initial_config():
            #Aqui con el if validamos que el usuario haya mandado correctamente los datos (parametros)
            #Tiene que regresar un TRUE esto significa que se devuelve un true es que 
            #Se actualizaron los parametros sin problema
            threading.Thread(target=self.listen_for_updates, daemon=True).start()
            #Se inicia un hilo (osea un proceso) para recibir las actualizaciones de los parametros

            self.stream_signal()
            #Y en hilo actual (el primer proceso se mandara y empezara a mandar señales senoidal)

            #===============================================================================#
            # Esta funcion es muy impotante ya que se manejan 2 hilos (osea 2 procesos)     #
            # Esta funcion recibe 2 tipos de hilos:                                         #
            # 1. El hilo que recibe los parametros de configuracion inicial del cliente     #
            # 2. El hilo que escucha las actualizaciones de los parametros en tiempo real   #
            # 3. El hilo que transmite la señal senoidal al cliente                         #
            #===============================================================================#


# ========================== #
#     CLASE: TCPServer       #
# ========================== #

class TCPServer:
    def __init__(self, host=HOST, port=TCP_PORT):
        self.host = host
        self.port = port
        
        self.running = False
        signal.signal(signal.SIGINT, self.signal_handler)


    def signal_handler(self, signum, frame):
        print("\n[SERVER] Interrupción recibida, cerrando el servidor...")
        self.running = False
        #Aqui se maneja la señal de interrupción (Ctrl+C) para cerrar el servidor de forma segura
        
        
    def start(self):
        self.running = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            server.listen()
            server.settimeout(1.0)
            print(f"[SERVER] TCP escuchando en {self.host}:{self.port}")
            while self.running:
                
                try:
                    conn, addr = server.accept()
                    handler = TCPHandler(conn, addr)
                    threading.Thread(target=handler.handle, daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[SERVER] Error al aceptar conexión: {e}")

# =========================== #
#       MAIN: Run server      #
# =========================== #
""""
if __name__ == "__main__":
    tcp_server = TCPServer()
    tcp_thread = threading.Thread(target=tcp_server.start, daemon=True)
    tcp_thread.start()

    # Solo el servidor TCP, no WebSocket ni FastAPI
    tcp_thread.join()  # Para que el hilo principal espere al servidor TCP
    
"""
if __name__ == "__main__":
    tcp_server = TCPServer()
    tcp_thread = threading.Thread(target=tcp_server.start)
    tcp_thread.start()

    try:
        while tcp_thread.is_alive():
            time.sleep(0.5)
            #
    except KeyboardInterrupt:
        print("\n[MAIN] KeyboardInterrupt recibido, cerrando...")
        tcp_server.running = False
        tcp_thread.join()
        
        #Descargar WSL UBUNTU LTS 24.04 
        #CPU NUCLEOS
