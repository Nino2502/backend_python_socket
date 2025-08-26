from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
import socket
import json
import time
import math
import asyncio
from typing import List

#____________________________________________________#
HOST = "0.0.0.0"
PORT = 8001
#____________________________________________________#


app = FastAPI()
active_connections: List[WebSocket] = []

@app.websocket("/ws/datos") #Se va aconectar a este endpoint
async def websocket_endpoint(websocket: WebSocket):
    
    await websocket.accept() #aqui solo se acepta la peticion Socket
    
    active_connections.append(websocket) #Aqui solo guardamos la IP y las conexiones
    
    try:
        while True:
            await websocket.receive_text()
           
            #Mantiene un bucle infinito esperando del cliente.
            
    except WebSocketDisconnect:
        
        #Se captura la expection
        
        active_connections.remove(websocket)
    
        #Solo removemos la conexion de active_connections para no enviar
        #datos en el futuro
        
async def broadcast_data(data):
    #Aqui solo enviamos los mensajes a todos los clientes WebSocket
    for connection in active_connections:
        #Recorre todas las conexiones activas guardadas en la lista
        try:
            
            await connection.send_json(data)
            
            #Envia los datos en formato JSON
        except:
            active_connections.remove(connection)
            
            #Si hay un error al enviar (por ejemplo, si el cliente ya se desconectó)

def start_tcp_server():    
    #Se creamos un socket TCP/IP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:

        #Asociamos el socket al host y puerto definidos previamente (HOST, PORT)
        server.bind((HOST, PORT))

        # Ponemos el socket en modo escucha para aceptar conexiones entrantes
        server.listen()
        
        print(f"Servidor TCP escuchando en {HOST}:{PORT}")
        
        # Esperamos a que un cliente se conecte y aceptamos la conexión
        conn, addr = server.accept()

        # Usamos el contexto 'with' para manejar la conexión entrante
        with conn:

            print(f"Conexión establecida con {addr}")
            
            # Frecuencia de transmisión de datos en Hertz (1 dato por segundo)
            hz = 10
            
            # Intervalo de tiempo entre muestras (1 segundo)
            ts = 1 / hz
            
            # Número total de paquetes a enviar
            cantidad_paquetes = 100
            
            # Tiempo total estimado de la transmisión
            total_time = cantidad_paquetes / hz

            # Creamos un nuevo loop de eventos asincrónicos para el hilo
            loop = asyncio.new_event_loop()

            #Asignamos el nuevo loop como el actual en este hilo
            asyncio.set_event_loop(loop)

            #Bucle para enviar todos los paquetes de datos
            for i in range(cantidad_paquetes):
                
                # Calculamos el valor de la onda senoidal en el instante actual
                y = math.sin(ts * i * 2 * math.pi)

                datos = {
                    "cantidad_paquetes": cantidad_paquetes,
                    "tiempo_esperado": total_time,
                    "x_paquetes": ts,
                    "hz": hz,
                    "ts": ts
                }

                coordenadas = {
                    "x": round(i * ts, 2),
                    "y": round(y, 4),
                    "ts_server": time.time()
                }
                
                # Combinamos ambos arreglos en uno solo
                data = {**datos, **coordenadas}
                
                 # Serializamos los datos a JSON y agregamos un salto de línea (para TCP)
                mensaje = json.dumps(data) + "\n"
                
                
                # Enviamos el mensaje codificado por la conexión TCP
                conn.sendall(mensaje.encode('utf-8'))


                # Enviamos los mismos datos a todos los clientes WebSocket conectados
                loop.run_until_complete(broadcast_data(data))
                
                #Esperamos el tiempo correspondiente antes de enviar el siguiente paquete

                time.sleep(ts)

            print("Transmisión finalizada")
            
            # Cerramos la conexión TCP con el cliente
            conn.close()

if __name__ == "__main__":
    import uvicorn
    import threading

    tcp_thread = threading.Thread(target=start_tcp_server)
    tcp_thread.daemon = True
    tcp_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    
