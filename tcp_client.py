import socket
import json
import time

HOST = "127.0.0.1"
PORT = 8001

latencias = []
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Conectado al servidor TCP")

    buffer = ""
    prev_ts_client = None

    while True:
        data = s.recv(1024)
        if not data:
            break

        buffer += data.decode('utf-8')

        while '\n' in buffer:
            linea, buffer = buffer.split('\n', 1)

            try:
                paquete = json.loads(linea.strip())
                ts_client = time.time()

                # Calcular tiempo entre paquetes recibidos en el cliente
                if prev_ts_client is not None:
                    diff_client = ts_client - prev_ts_client
                    print(f"[CLIENTE] Δt entre paquetes recibidos: {diff_client:.6f} segundos")
                else:
                    print("[CLIENTE] Primer paquete recibido")
                prev_ts_client = ts_client

                # Calcular latencia real (ts_client - ts_server)
                ts_server = paquete.get("ts_server")
                if ts_server:
                    latencia = ts_client - ts_server
                    latencias.append(latencia)
                    print(f"[LATENCIA] Desde el servidor hasta cliente: {latencia:.6f} segundos")

                # Mostrar información adicional
                print(f"[PAQUETE] Número: {paquete.get('cantidad_paquetes')} | Tiempo transcurrido: {paquete.get('tiempo_transcurrido')}s")
                print(f"[RECURSOS] CPU total: {paquete.get('cpu_equipo_total')}%, RAM total: {paquete.get('ram_equipo_total')}%")
                print(f"[DELTA_T] Tiempo entre envíos en servidor: {paquete.get('delta_t')} segundos")

                if paquete.get('fin') == True:
                    print("\n[FINAL] Transmisión finalizada.")
                    print(f"Cantidad total de paquetes: {paquete.get('cantidad_paquetes')}")
                    if latencias:
                        print(f"Latencia promedio: {sum(latencias)/len(latencias):.6f} s")
                        print(f"Latencia mínima: {min(latencias):.6f} s")
                        print(f"Latencia máxima: {max(latencias):.6f} s")
                    break

                print("*" * 80)

            except json.JSONDecodeError:
                print("Error al decodificar JSON:", linea.strip())
