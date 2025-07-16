import socket
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


def get_resource_usage():
    process = psutil.Process()
    process.cpu_percent(interval=None)
    
    return {
        "cpu_process_percent": round(process.cpu_percent(interval=None), 2),
        "cpu_equipo_total": round(psutil.cpu_percent(interval=None), 2),
        "ram_process_mb": round(process.memory_info().rss / (1024 * 1024), 2),
        "ram_equipo_total": round(psutil.virtual_memory().percent, 2),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "nucleos_fisicos": psutil.cpu_count(logical=False)
    }
    
      #Y despues basicamente lo retorno con un array lleno de objectos con los datos de uso de recursos
    #Psra acceder a los datos con la funcion de mandar datos por socket


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
        
        self.params = {
            "amplitud": 30.0, 
            "hz": 100.0, 
            "stop": False, 
            "segundos": 10.0, 
            "hz_m": 10.0
        }
        self.lock = threading.Lock()
        #Este es unlock que ayuda a proteger la lectura y la escritura de los parámetros (osea editar los parámetros)
        #Cuando se modifican desde múltiples hilos, evitando condiciones de carrera.
        
        
        self.start_time = time.time()

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
                self.params.update({
                    "amplitud": float(config.get("amplitud", self.params["amplitud"])),
                    "hz": float(config.get("hz", self.params["hz"])),
                    "segundos": float(config.get("segundos", self.params["segundos"])),
                    "hz_m": float(config.get("hz_m", self.params["hz_m"]))
                })
            return True
        except Exception as e:
            print(f"[SERVER] Error en configuración inicial: {e}")
            self.conn.close()
            return False

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
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    try:
                        msg = json.loads(linea.strip())
                        with self.lock:
                            self.params.update({
                                "amplitud": float(msg.get("amplitud", self.params["amplitud"])),
                                "hz": float(msg.get("hz", self.params["hz"])),
                                "segundos": float(msg.get("segundos", self.params["segundos"])),
                                "hz_m": float(msg.get("hz_m", self.params["hz_m"]))
                            })
                            if msg.get("stop"):
                                self.params["stop"] = True
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                print(f"[SERVER] Error recibiendo parámetros: {e}")
                break

    def stream_signal(self):

        cantidad_paquetes = 0
        #AQUI DECLARAMOS DOS VARIABLES DE TIEMPO PARA 
        #PAra calcular el envio del primer paquete


        next_sample_time = time.time()
        last_debug_time = time.time()
        
        try:
            while not self.params["stop"]:
                current_time = time.time()
                
                # Si aun no llegamos al momento de graficar
                # Como detenemos el tiempo restante ( ~ 1 ms para compensar que se tarde los paquetes)
                
                # Espera hasta el próximo intervalo
                # Esta parte del codigo, solo calculamos el tiempo para mandar el siguiente paquete
                # Se le resta 0.001 por precaucion, osea para que se despiera o se detenga
                # antes de 1 milesgundos antes.
                
                if current_time < next_sample_time:
                    time.sleep(max(0, next_sample_time - current_time - 0.001))
                    continue
                
                
                # Aqui es hora enviar el siguiente paquete
                # Bloque sincronizado para parámetros
                with self.lock:
                    
                    #ts es el tiempo que hay entre cada paquete de hz_muestreo
                    ts = 1.0 / self.params["hz_m"] 
                    amplitud = self.params["amplitud"]
                    hz = self.params["hz"]
                    
                    #Calculamos cuanto tiempo ha pasado desde el inicio que se llego en la funcion
                    elapsed = current_time - self.start_time
                
                # le sumamos el "marcador" de tiempo ideal en un ts (1/hz_m)
                #Aqui tiene que ir concidiendo el ts con el tiempo que va en next_sample_time
                next_sample_time += ts
                
                # Generación de señal
                y = amplitud * math.sin(2 * math.pi * hz * elapsed)
                
                # Obtener métricas reales del sistema
                #recursos = get_resource_usage()
                
                recursos =  {
                        "cpu_process_percent": 2,
                        "cpu_equipo_total": 1,
                        "ram_process_mb": 2,
                        "ram_equipo_total": 3,
                        "nucleos_logicos":3,
                        "nucleos_fisicos": 2
                    }
                
                # Construcción del paquete
                data = {
                    "cantidad_paquetes": cantidad_paquetes,
                    "tiempo_transcurrido": round(elapsed, 4),
                    "hz": hz,
                    "ts": ts,
                    "hz_m": self.params["hz_m"],
                    "segundos": self.params["segundos"],
                    "x": round(elapsed, 4),
                    "y": round(y, 4),
                    "ts_server": current_time,
                    "delta_t": round(ts, 6),
                    **recursos
                }
                
                # Envío sin delay adicional
                self.conn.sendall((json.dumps(data) + "\n").encode("utf-8"))
                cantidad_paquetes += 1
                
                # Log de diagnóstico (cada 1 segundo)
                if current_time - last_debug_time >= 1.0:
                    print(f"[SERVER] Paquetes: {cantidad_paquetes} | Retraso: {current_time - next_sample_time:.6f}s")
                    last_debug_time = current_time
                    
        except BrokenPipeError:
            print(f"[SERVER] Cliente {self.addr} desconectado")
        except Exception as e:
            print(f"[SERVER] Error en stream_signal: {str(e)}")
        finally:
            self.conn.close()

    def handle(self):
        print(f"[SERVER] Nueva conexión desde {self.addr}")
        if self.receive_initial_config():
            threading.Thread(target=self.listen_for_updates, daemon=True).start()
            self.stream_signal()

class TCPServer:
    def __init__(self, host=HOST, port=TCP_PORT):
        self.host = host
        self.port = port
        self.running = False
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        print("\n[SERVER] Cerrando servidor...")
        self.running = False
        
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

if __name__ == "__main__":
    tcp_server = TCPServer()
    tcp_thread = threading.Thread(target=tcp_server.start)
    tcp_thread.start()

    try:
        while tcp_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[MAIN] Deteniendo servidor...")
        tcp_server.running = False
        tcp_thread.join()