import csv
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import socket
import json
import tkinter as tk
from tkinter import messagebox
import time 
from ttkbootstrap import Style


import matplotlib.pyplot as plt


class AppWindow(ttk.Window):
    def __init__(self):
        super().__init__(themename="cyborg")  # Cambia a otros temas como "superhero", "flatly", "journal", etc.
        self.title("Monitor TCP/IP - Realtime Signals")
        self.geometry("1280x720")

        # Variables para los parámetros de la señal
        self.amplitud = 0
        self.hz = 0
        self.segundos = 0
        
        self.max_datos = 20
        
        
        self.data = []
        
        self.BUFFER_SIZE = 4096  # Buffer size for receiving data

        

        self.historial_datos = []


        # Datos para las gráficas
        self.x_data, self.y_data, = [], []
        
        self.x1_data, self.y1_data = [], []
        
        
        self.x2_data, self.y2_data = [], []
        
          
          
        self.tcp_socket = None
        
        self.recibiendo_datos = False
        self.hilo_recepcion = None

        

    

        # Contenedor principal con scrollbar
        self.canvas_frame = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas_frame.yview)
        self.canvas_frame.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scroll_frame = ttk.Frame(self.canvas_frame)
        self.window_id = self.canvas_frame.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas_frame.bind("<Configure>", lambda e: self.canvas_frame.itemconfig(self.window_id, width=e.width))
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas_frame.configure(scrollregion=self.canvas_frame.bbox("all")))

        self.inner_frame = ttk.Frame(self.scroll_frame, padding=20)
        self.inner_frame.pack(fill='both', expand=True)

        # Título
        ttk.Label(self.inner_frame, text="Monitoreo de Señales TCP/IP", font=("Segoe UI", 28, "bold"), bootstyle="info").pack(pady=10)

        # Gráfico
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.inner_frame)
        self.canvas.get_tk_widget().pack(pady=10, fill='both', expand=True)
        
        # Contenedor de controles
        controles_frame = ttk.Labelframe(self.inner_frame, text="Configuración de Señal", bootstyle="primary", padding=15)
        controles_frame.pack(fill='x', pady=10)

        # Permitir que las columnas se expandan (responsive)
        for i in range(12):
            controles_frame.grid_columnconfigure(i, weight=1)  # Hace que cada columna pueda crecer si hay espacio

        # Row 0: Amplitud
        ttk.Label(controles_frame, text="Amplitud:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.entrada_amplitud = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 10))
        self.entrada_amplitud.insert(0, str(self.amplitud))
        self.entrada_amplitud.grid(row=0, column=1, sticky='ew', padx=5)
        

        # Hz
        ttk.Label(controles_frame, text="Hz:", font=("Segoe UI", 12)).grid(row=0, column=3, sticky='e', padx=5)
        self.entrada_hz = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 10))
        self.entrada_hz.insert(0, str(self.hz))
        self.entrada_hz.grid(row=0, column=4, sticky='ew', padx=5)
     

        """"
        # Segundos
        ttk.Label(controles_frame, text="Segundos:", font=("Segoe UI", 12)).grid(row=0, column=6, sticky='e', padx=5)
        self.entrada_segundos = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 10))
        self.entrada_segundos.insert(0, str(self.segundos))
        self.entrada_segundos.grid(row=0, column=7, sticky='ew', padx=5)
       
       """
        # Iniciar Monitoreo
        ttk.Button(controles_frame, text="Iniciar Monitoreo", bootstyle='success outline', width=60, command=self.start_client).grid(
            row=0, column=9, padx=5, pady=5, sticky='ew')

        # Detener Monitoreo
        ttk.Button(controles_frame, text="Detener Monitoreo", bootstyle='danger outline', width=60, command=self.stop_monitor).grid(
            row=0, column=10, padx=5, pady=5, sticky='ew')
        
        
        # Contenedor para las gráficas
        grafica_frame = ttk.Labelframe(self.inner_frame, text="Visualización de Señales", bootstyle="danger", padding=20)
        grafica_frame.pack(fill='both', pady=10, expand=True)

        # Frame interno para colocar las gráficas lado a lado
        graficas_row = ttk.Frame(grafica_frame)
        graficas_row.pack(fill='both', expand=True)

        # Configura columnas para que se expandan
        graficas_row.columnconfigure(0, weight=1)
        graficas_row.columnconfigure(1, weight=1)
        graficas_row.rowconfigure(0, weight=1)

        # Gráfica 1 (más pequeña, pero expandible)
        

                                
        self.fig1, self.ax1 = plt.subplots(figsize=(5, 3))
        self.ax1.set_title("Señales RAM")   
        
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=graficas_row)
        self.canvas1.get_tk_widget().grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        # Gráfica 2 (también expandible)
        
        self.fig2, self.ax2 = plt.subplots(figsize=(5, 3))
        self.ax2.set_title("Señales CPU")
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=graficas_row)
        self.canvas2.get_tk_widget().grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        
        
        # Contenedor para las gráficas
        descargar_frame = ttk.Labelframe(self.inner_frame, text="Descargar archivo CSV", bootstyle="primary", padding=20)
        descargar_frame.pack(fill='both', pady=10, expand=True)

        # Botón para descargar CSV
        ttk.Button(
            descargar_frame,
            text="Descargar Archivo CSV",
            bootstyle='success outline',
            command=self.descargar_csv
        ).pack(fill='x', expand=True, pady=10)
        


    def start_client(self):
        goValidation = True
        HOST = "127.0.0.1"
        PORT = 8001
        
        try:
            self.amplitud = float(self.entrada_amplitud.get())
            
            self.amplitud = max(0, self.amplitud)
            
            if self.amplitud == 0:
                messagebox.showerror("Error", "La amplitud no puede ser cero.")
                goValidation = False
                return
            if self.amplitud < 0:
                messagebox.showerror("Error", "La amplitud no puede ser negativa.")
                goValidation = False
                return
            
            
            print(f"Amplitud actualizada a: {self.amplitud}")
        except ValueError:
            messagebox.showerror("Error","Valor no válido para amplitud")
            goValidation = False
        try:
            self.hz = float(self.entrada_hz.get())
            
            if self.hz == 0:
                messagebox.showerror("Error","La hz no puede ser cero.")
                goValidation = False
                return
            
            if self.hz < 0:
                messagebox.showerror("Error", "La hz no puede ser negativa.")
                goValidation = False
                return
            
            print(f"Hz actualizado a: {self.hz}")
        except ValueError:
            messagebox.showerror("Error","Valor no válido para Hz")
            goValidation = False



        if goValidation == True: 
            
            self.x_data, self.y_data, = [], []
        
            self.x1_data, self.y1_data = [], []
        
        
            self.x2_data, self.y2_data = [], []
            
            
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s = self.tcp_socket
            
            try:
                print("Se va a conectar al servidor")
                #Aqui se va a conectar al servidor Socket
                s.connect((HOST, PORT))
                
                init_config = {
                    "amplitud": self.amplitud,
                    "hz": self.hz,
                }
                #Aqui mandamos la primera configuracion inicial para hacer las graficas senoidales
                #Estos datos de mandara al archivo tcp_server_tiempo en la funcion [ **def receive_initial_config(self)** ]                
                s.sendall((json.dumps(init_config) + '\n').encode('utf-8'))
                
                print(f"[CLIENT] Connected to {HOST} : {PORT} AYUDA POR FAVOR !!!!!!!!")
                
                
                #Aqui el cliente recibe datos en tiempo real
                recibir_trama = threading.Thread(target=self.recibir_data, args=(s,))
                recibir_trama.daemon = True
                recibir_trama.start()
                #Aqui este hilo manda a llamar a mostrar_information() que recibe los datos del servidor
                #y los procesa para actualizar las graficas
                
                
                
                #Este hilo se ejecuta en el cliente
                send_thread = threading.Thread(target=self.send_parameters, args=(s,))
                send_thread.daemon = True
                send_thread.start()
                
                #=======================================#
                #  En la funcion en la send_parameters se envia el mensaje al servidor cada segundo
                # Y esta funcion se mandara al servidor en la funcion listen_for_updates() 
                # Y se actulizan los valores con self.lock
                """""
                {
                    "amplitud": ..., 
                    "hz": ..., 
                    "segundos": ...
                    #Esta informacion se envia al servidor cada segundo
                    
                }
                """""
  
            except ConnectionRefusedError:
                print("No se logro conectar al servidor TCP :c ")

            #t = threading.Thread(target=self.listen_tcp)
            #t.daemon = True
            #t.start()
            #print(f"Iniciando monitoreo con amplitud={self.amplitud}, hz={self.hz}, segundos={self.segundos}")
            #self.iniciar_monitor_alert()

    
    def recibir_data(self, socket):
        try:
            print("Entre en 1")
          
            
            while True:
                print("Entre al while por favor")
                
                received_message = self.mostrar_information(socket)

                if received_message is None:
                    print("[CLIENT] Server disconnected or error during receive.")
                    break # Exit the loop and thread

                try:
                    signal_data = json.loads(received_message)
                    
                    print(f"[CLIENT] Received data: ")
                    x = signal_data.get("x")
                    
                    y = signal_data.get("y")
                    
                    print(f"[CLIENT] Coordenadas X: {x}, Y: {y}")
                    
                    
                    self.historial_datos.append({
                            "cantidad_paquetes": signal_data.get("cantidad_paquetes", 0),
                            "tiempo": signal_data.get("tiempo_transcurrido",""),
                            "hz": signal_data.get("hz", 0),
                            "x_paquetes": signal_data.get("delta_t", ""),
                            "cpu_percent": signal_data.get("cpu_process_percent", ""),
                            "cpu_equipo_total": signal_data.get("cpu_equipo_total", ""),
                            "ram_mb": signal_data.get("ram_process_mb", ""),
                            "ram_equipo_total": signal_data.get("ram_equipo_total", ""),
                            "vs_code_ram": signal_data.get("vs_code_ram", ""),
                            "cmd_exe_ram": signal_data.get("cmd_ram", "")
                    })
                    
                                            
                    ram = signal_data.get("ram_equipo_total")
                    cpu = signal_data.get("cpu_equipo_total", 0)

                    if x is not None and y is not None:


                            self.x_data.append(x)
                            self.y_data.append(y)
                            self.x_data = self.x_data[-self.max_datos:]
                            self.y_data = self.y_data[-self.max_datos:]
                            self.ax.clear()
                            self.ax.plot(self.x_data, self.y_data, color='red', label='Señal Y')
                            self.ax.set_title("Señales Recibidas")
                            self.ax.set_xlabel("Tiempo")
                            self.ax.set_ylabel("Amplitud")
                            self.ax.legend()
                            self.canvas.draw()

                            # RAM
                            self.x1_data.append(x)
                            self.y1_data.append(ram)
                            self.x1_data = self.x1_data[-self.max_datos:]
                            self.y1_data = self.y1_data[-self.max_datos:]
                            self.ax1.clear()
                            self.ax1.plot(self.x1_data, self.y1_data, color='blue', label='RAM Total')
                            self.ax1.set_title("Uso de RAM")
                            self.ax1.set_xlabel("Tiempo")
                            self.ax1.set_ylabel("RAM (MB)")
                            self.ax1.legend()
                            self.canvas1.draw()

                            # CPU
                            self.x2_data.append(x)
                            self.y2_data.append(cpu)
                            self.x2_data = self.x2_data[-self.max_datos:]
                            self.y2_data = self.y2_data[-self.max_datos:]
                            self.ax2.clear()
                            self.ax2.plot(self.x2_data, self.y2_data, color='green', label='CPU Total')
                            self.ax2.set_title("Uso de CPU")
                            self.ax2.set_xlabel("Tiempo")
                            self.ax2.set_ylabel("CPU (%)")
                            self.ax2.legend()
                            self.canvas2.draw()

        
                except json.JSONDecodeError:
                    print(f"[CLIENT] Could not decode JSON: {received_message}")
        
                except Exception as e:
                    print(f"[CLIENT] Error processing received data: {e}")

        
        except Exception as e:
            print(f"[CLIENT] Error in receive_data: {e}")
            print("Entre en 2 cliente")
        finally:
            print("[CLIENT] Stopped receiving data.")

    def mostrar_information(self, conn):
        buffer = ""
        while True:
            try:
                #print("[CLIENT] Esperando datos del servidor...")  # 👈 ¿Se imprime esto?
                data = conn.recv(self.BUFFER_SIZE)
                #print(f"[CLIENT] Datos crudos recibidos: {data}")  # 👈 ¿Se imprime esto?

                if not data:
                    #print("[CLIENT] No more data received, closing connection.")
                    return None

                decoded = data.decode('utf-8')
                #print(f"[CLIENT] Datos decodificados: {decoded}")
                buffer += decoded

                if '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    #print(f"[CLIENT] Línea completa: {line.strip()}")
                    return line.strip()

            except Exception as e:
                print(f"[CLIENT] Error receiving data: {e}")
                return None

    def send_parameters(self, socket):
        while True:
            try:
                # Leer los valores de las entradas
                amplitud = self.entrada_amplitud.get()
                hz = self.entrada_hz.get()   
                
                # Crear el mensaje JSON
                message = {
                    "amplitud": amplitud,
                    "hz": hz,
                } 
                
                # Enviar el mensaje al servidor
                socket.sendall((json.dumps(message) + '\n').encode('utf-8'))
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[CLIENT] Error sending parameters: {e}")
                break
    
    
   

    def run(self):
        self.mainloop()
        
    def stop_monitor(self):
        print("Deteniendo monitoreo...")
        if self.tcp_socket:
            try:
                stop_msg = json.dumps({"stop": True}) + "\n"
                self.tcp_socket.sendall(stop_msg.encode("utf-8"))
                print("Comando STOP enviado.")
            except Exception as e:
                print(f"Error al enviar comando STOP: {e}")
            finally:
                try:
                    self.tcp_socket.close()
                except:
                    pass
                self.tcp_socket = None
        else:
            print("No hay socket TCP activo.")

    def descargar_csv(self):
        #messagebox.showinfo("Descargar CSV","Descargando archivo csv....")

        if not self.historial_datos:
            messagebox.showwarning("Advertencia", "No hay datos para descargar.")
            return
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Guardar CSV"
        )
        
        if not archivo:
            return
        
        headers = ['#', 'Cantidad (paquetes)', 
               'Tiempo (ms) REAL', 
               'Hz Velocidad', 
               'Diferencia segundos paquetes',
               'cpu_percent','cpu_equipo_total','ram_percent','ram_total_equipo',
               'vs_code_ram', 'cmd_exe_ram']
        
        
        try:
            with open(archivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

                for idx, row in enumerate(self.historial_datos, 1):
                    writer.writerow([
                        idx,
                        row["cantidad_paquetes"],
                        row["tiempo"],
                        row["hz"],
                        row["x_paquetes"],
                        row["cpu_percent"],
                        row["cpu_equipo_total"],
                        row["ram_mb"],
                        row["ram_equipo_total"],
                        row["vs_code_ram"],
                        row["cmd_exe_ram"]
                    ])
            messagebox.showinfo("Éxito", "Archivo CSV exportado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo CSV: {e}")
            

if __name__ == '__main__':
    app = AppWindow()
    app.run()

    
    
    
    
    
