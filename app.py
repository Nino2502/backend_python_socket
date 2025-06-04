from fastapi import FastAPI, WebSocket
import math
import asyncio
import time

app = FastAPI()



@app.websocket("/ws/sine")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    cantidad_paquetes = 100
    """
    Esta variable define la cantidad total de paquetes que se van a mandar 
    al frontend a través del protocolo WebSocket.
    """
    """"""
    hz = 90
    """
    Esta variable indica la frecuencia de muestreo en hercios (Hz),
    es decir, cuántos paquetes se mandarán por segundo.
    """
    ts = 1 / hz
    """
    Esta variable es el intervalo de tiempo entre cada paquete.
    Por ejemplo, si hz = 10, entonces ts = 0.1 s (100 ms),
    lo cual significa que se enviará un paquete cada 0.1 segundos.
    """
    total_time = cantidad_paquetes / hz
    """
    Esta variable representa el tiempo total estimado que se tardará
    en enviar todos los paquetes, con base en la frecuencia hz.
    """

    i = 0  # Esta variable es usada como marcador para el eje x en la gráfica de la señal senoidal
    
    
    count = 0  # Contador de paquetes enviados al frontend



    t0 = time.time()  # Marcar el tiempo de inicio para medir la duración real del envío
    while count < cantidad_paquetes:
        """
        El bucle se ejecutará hasta que se hayan enviado la cantidad total
        de paquetes definidos en 'cantidad_paquetes'.
        """
        y = math.sin(ts * i * 2 * math.pi)  # Generar la señal senoidal usando la fórmula y = sin(2πft)
        await websocket.send_json({
            "cantidad_paquetes": cantidad_paquetes,  # Cantidad total de paquetes a enviar
            "tiempo_p": total_time,               # Tiempo total estimado de la prueba
            "x": round(i, 2),                     # Valor del eje x (tiempo relativo)
            "y": round(y, 4),                     # Valor del eje y (señal senoidal)
            "hz": hz,                             # Frecuencia de muestreo
            "x_paquetes": ts,                     # Tiempo entre cada paquete
            "ts_server": t0,                      # Timestamp inicial para medir rendimiento
            "tiempo_esperado": total_time         # Tiempo que se debería tardar en teoría
        })
        i += 1          # Aumentar el marcador de tiempo
        count += 1      # Aumentar el contador de paquetes enviados
        await asyncio.sleep(ts)
        """
        Esperar 'ts' segundos antes de enviar el siguiente paquete.
        Esta espera es lo que simula la frecuencia de muestreo.
        Por ejemplo, si ts = 0.0025, se espera 2.5 ms entre cada envío.
        """


    
    
    
    ##CORRER PROYECTO: uvicorn app:app --reload

