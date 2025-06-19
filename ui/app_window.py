
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import socket
import json
import tkinter as tk
from tkinter import messagebox

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

        # Datos para las gráficas
        self.x_data, self.y_data, = [], []
        
        self.x1_data, self.y1_data = [], []
        
        
        self.x2_data, self.y2_data = [], []
        
          
          
        self.tcp_socket = None
        
    

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
        self.entrada_amplitud = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 12))
        self.entrada_amplitud.insert(0, str(self.amplitud))
        self.entrada_amplitud.grid(row=0, column=1, sticky='ew', padx=5)
        ttk.Button(controles_frame, text="Actualizar", bootstyle='success', command=self.actualizar_amplitud).grid(row=0, column=2, sticky='ew', padx=5)

        # Hz
        ttk.Label(controles_frame, text="Hz:", font=("Segoe UI", 12)).grid(row=0, column=3, sticky='e', padx=5)
        self.entrada_hz = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 12))
        self.entrada_hz.insert(0, str(self.hz))
        self.entrada_hz.grid(row=0, column=4, sticky='ew', padx=5)
        ttk.Button(controles_frame, text="Actualizar", bootstyle='warning', command=self.actualizar_hz).grid(row=0, column=5, sticky='ew', padx=5)

        # Segundos
        ttk.Label(controles_frame, text="Segundos:", font=("Segoe UI", 12)).grid(row=0, column=6, sticky='e', padx=5)
        self.entrada_segundos = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 12))
        self.entrada_segundos.insert(0, str(self.segundos))
        self.entrada_segundos.grid(row=0, column=7, sticky='ew', padx=5)
        ttk.Button(controles_frame, text="Actualizar", bootstyle='danger', command=self.actualizar_seg).grid(row=0, column=8, sticky='ew', padx=5)

        # Iniciar Monitoreo
        ttk.Button(controles_frame, text="Iniciar Monitoreo", bootstyle='success outline', width=65, command=self.start_thread).grid(
            row=0, column=9, padx=5, pady=5, sticky='ew')

        # Detener Monitoreo
        ttk.Button(controles_frame, text="Detener Monitoreo", bootstyle='danger outline', width=65, command=self.stop_monitor).grid(
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

    # Actualizadores
    def actualizar_amplitud(self):
        try:
            self.amplitud = float(self.entrada_amplitud.get())
            print(f"Amplitud actualizada a: {self.amplitud}")
        except ValueError:
            print("Valor no válido para amplitud")

    def actualizar_hz(self):
        try:
            self.hz = float(self.entrada_hz.get())
            print(f"Hz actualizado a: {self.hz}")
        except ValueError:
            print("Valor no válido para Hz")

    def actualizar_seg(self):
        try:
            self.segundos = float(self.entrada_segundos.get())
            print(f"Segundos actualizados a: {self.segundos}")
        except ValueError:
            print("Valor no válido para segundos")

    def start_thread(self):
        
        goValidation = True
        
        
        if self.segundos <= 0:
            messagebox.showerror("Error", "El valor de segundos debe ser mayor que 0.")
            goValidation = False
            
        if self.hz <= 0:
            messagebox.showerror("Error", "El valor de Hz debe ser mayor que 0.")
            goValidation = False
            
        if self.amplitud <= 0:
            messagebox.showerror("Error", "El valor de amplitud debe ser mayor que 0.")
            goValidation = False            


        if goValidation == True:
            t = threading.Thread(target=self.listen_tcp)
            t.daemon = True
            t.start()
            print(f"Iniciando monitoreo con amplitud={self.amplitud}, hz={self.hz}, segundos={self.segundos}")
            self.iniciar_monitor_alert(self)

    def listen_tcp(self):
        HOST = "127.0.0.1"
        PORT = 8001
        buffer = ""

        # Guardamos el socket en la instancia para acceder desde stop_monitor
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = self.tcp_socket

        try:
            s.connect((HOST, PORT))
            config = {
                "amplitud": self.amplitud,
                "hz": self.hz,
                "segundos": self.segundos
            }
            s.sendall((json.dumps(config) + '\n').encode('utf-8'))

            while True:
                data = s.recv(1024)
                if not data:
                    break
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    linea, buffer = buffer.split('\n', 1)
                    try:
                        paquete = json.loads(linea.strip())
                        x = paquete.get("x")
                        y = paquete.get("y")
                        ram = paquete.get("ram_equipo_total")
                        cpu = paquete.get("cpu_equipo_total", 0)

                        if x is not None and y is not None:
                            # Gráfica senoidal
                            self.x_data.append(x)
                            self.y_data.append(y)
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
                            self.ax2.clear()
                            self.ax2.plot(self.x2_data, self.y2_data, color='green', label='CPU Total')
                            self.ax2.set_title("Uso de CPU")
                            self.ax2.set_xlabel("Tiempo")
                            self.ax2.set_ylabel("CPU (%)")
                            self.ax2.legend()
                            self.canvas2.draw()

                        if paquete.get("fin"):
                            print("Transmisión finalizada por el servidor.")
                            return
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error en conexión TCP: {e}")
        finally:
            if self.tcp_socket:
                try:
                    self.tcp_socket.close()
                except:
                    pass
                self.tcp_socket = None


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

    
    
    def iniciar_monitor_alert(self, event):
        messagebox.showinfo("Monitoreo Iniciado", "El monitoreo ha comenzado exitosamente.")
        
        self.listen_tcp(self)
        


if __name__ == '__main__':
    app = AppWindow()
    app.run()
