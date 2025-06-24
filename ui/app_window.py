"""
CLIENTE TCP PARA MONITOREO DE SEÑALES EN TIEMPO REAL
Autor: [Tu Nombre]
Fecha: [Fecha]
Descripción: Este programa conecta con un servidor TCP para recibir y graficar señales senoidales
             junto con métricas de sistema (CPU/RAM) en tiempo real.
"""
import csv
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import socket
import json
import time
import tkinter as tk

class AppWindow(ttk.Window):
    def __init__(self):
        super().__init__(themename="cyborg")
        self.title("Monitor TCP/IP - Realtime Signals")
        self.geometry("1280x720")

        # ============================== #
        #     VARIABLES DE CONFIGURACIÓN #
        # ============================== #
        self.amplitud = 0      # Amplitud de la señal senoidal
        self.hz = 0            # Frecuencia de la señal en Hz
        self.max_datos = 20    # Máximo de puntos mostrados en gráfica
        self.data_lock = threading.Lock()  # Lock para seguridad en hilos
        self.historial_datos = []  # Almacena todos los datos recibidos

        # Buffers para datos gráficos
        self.x_data, self.y_data = [], []    # Señal principal
        self.x1_data, self.y1_data = [], []  # Datos de RAM
        self.x2_data, self.y2_data = [], []  # Datos de CPU

        # ============================== #
        #     CONFIGURACIÓN DE SOCKET    #
        # ============================== #
        self.tcp_socket = None          # Socket TCP
        self.recibiendo_datos = False   # Flag para hilo de recepción
        self._refrescando = False       # Flag para actualización gráfica

        # Configuración de interfaz gráfica
        self._setup_ui()

    def _setup_ui(self):
        """Configura todos los elementos de la interfaz gráfica"""
        # ============================================= #
        #     ÁREA PRINCIPAL CON SCROLLBAR             #
        # ============================================= #
        self.canvas_frame = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas_frame.yview)
        self.canvas_frame.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Frame contenedor para los elementos con scroll
        self.scroll_frame = ttk.Frame(self.canvas_frame)
        self.window_id = self.canvas_frame.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        # Ajuste automático de tamaño
        self.canvas_frame.bind("<Configure>", lambda e: self.canvas_frame.itemconfig(self.window_id, width=e.width))
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas_frame.configure(scrollregion=self.canvas_frame.bbox("all")))

        # Frame interno para el contenido
        self.inner_frame = ttk.Frame(self.scroll_frame, padding=20)
        self.inner_frame.pack(fill='both', expand=True)

        # ============================================= #
        #     TÍTULO PRINCIPAL                         #
        # ============================================= #
        ttk.Label(self.inner_frame, 
                text="Monitoreo de Señales TCP/IP", 
                font=("Segoe UI", 28, "bold"), 
                bootstyle="info").pack(pady=10)

        # ============================================= #
        #     GRÁFICA PRINCIPAL (SEÑAL SENOIDAL)       #
        # ============================================= #
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.inner_frame)
        self.canvas.get_tk_widget().pack(pady=10, fill='both', expand=True)

        # ============================================= #
        #     PANEL DE CONTROL (PARÁMETROS)            #
        # ============================================= #
        controles_frame = ttk.Labelframe(self.inner_frame, 
                                       text="Configuración de Señal", 
                                       bootstyle="primary", 
                                       padding=15)
        controles_frame.pack(fill='x', pady=10)
        
        
        
        

        # Entrada para amplitud
        ttk.Label(controles_frame, text="Amplitud:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.entrada_amplitud = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 10))
        self.entrada_amplitud.insert(0, "10")
        self.entrada_amplitud.grid(row=0, column=1, sticky='ew', padx=5)

        # Entrada para frecuencia (Hz)
        ttk.Label(controles_frame, text="Hz:", font=("Segoe UI", 12)).grid(row=0, column=3, sticky='e', padx=5)
        self.entrada_hz = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 10))
        self.entrada_hz.insert(0, "10")
        self.entrada_hz.grid(row=0, column=4, sticky='ew', padx=5)

        # Botón para iniciar/actualizar monitoreo
        ttk.Button(controles_frame, 
                 text="Iniciar/Actualizar Monitoreo", 
                 bootstyle='success outline', 
                 command=self.start_client).grid(row=0, column=9, padx=5, pady=5, sticky='ew')

        # Botón para detener monitoreo
        ttk.Button(controles_frame, 
                 text="Detener Monitoreo", 
                 bootstyle='danger outline', 
                 command=self.stop_monitor).grid(row=0, column=10, padx=5, pady=5, sticky='ew')
        
        
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
            
        
          

    def start_client(self):
        """
        Maneja la conexión inicial y actualización de parámetros.
        - Valida los valores de entrada
        - Inicia nueva conexión o actualiza parámetros existentes
        """
        # Validación de parámetros
        try:
            new_amplitud = float(self.entrada_amplitud.get())
            new_hz = float(self.entrada_hz.get())
            if new_amplitud <= 0 or new_hz <= 0:
                raise ValueError("Los valores deben ser positivos")
        except Exception as e:
            messagebox.showerror("Error", f"Valores inválidos: {str(e)}")
            return

        # Conexión inicial o actualización
        if not self.tcp_socket:
            self._iniciar_conexion()
        else:
            self._enviar_parametros()

    def _iniciar_conexion(self):
        """
        Establece una nueva conexión TCP con el servidor:
        1. Crea el socket TCP
        2. Conecta al servidor
        3. Inicia hilo de recepción
        4. Activa actualización gráfica
        """
        try:
            # Configuración del socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect(("127.0.0.1", 8001))
            
            # Envía parámetros iniciales
            self._enviar_parametros()
            
            # Inicia hilo para recepción de datos
            self.recibiendo_datos = True
            threading.Thread(
                target=self.recibir_data, 
                args=(self.tcp_socket,), 
                daemon=True
            ).start()
            
            # Activa actualización gráfica si no estaba activa
            if not self._refrescando:
                self._refrescando = True
                self._actualizar_grafica()
                
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en conexión: {str(e)}")

    def _enviar_parametros(self):
        """Envía los parámetros actuales al servidor en formato JSON"""
        if self.tcp_socket:
            try:
                msg = {
                    "amplitud": float(self.entrada_amplitud.get()),
                    "hz": float(self.entrada_hz.get())
                }
                self.tcp_socket.sendall((json.dumps(msg) + '\n').encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Envío de parámetros: {e}")

    def recibir_data(self, socket):
        """
        Hilo para recepción continua de datos:
        1. Recibe datos en bruto del socket
        2. Decodifica mensajes JSON
        3. Almacena datos en buffers con seguridad de hilos
        """
        buffer = ""
        while self.recibiendo_datos:
            try:
                data = socket.recv(4096)
                if not data:  # Conexión cerrada
                    break
                    
                buffer += data.decode('utf-8')
                
                # Procesa todos los mensajes completos (separados por \n)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    datos = json.loads(line)
                    
                    # Almacenamiento seguro con lock
                    with self.data_lock:
                        self.x_data.append(datos["x"])
                        self.y_data.append(datos["y"])
                        
                        self.x1_data.append(datos["x"])
                        self.y1_data.append(datos["ram_equipo_total"])
                        
                        
                        self.x2_data.append(datos["x"])
                        self.y2_data.append(datos["cpu_equipo_total"])
                        
                        
                        self.historial_datos.append(datos)
                        
            except json.JSONDecodeError:
                print("[WARN] Mensaje JSON inválido recibido")
            except Exception as e:
                print(f"[ERROR] Recepción de datos: {e}")
                break

    def _actualizar_grafica(self):
        """
        Actualización periódica de la gráfica principal:
        1. Obtiene los últimos datos (con lock)
        2. Redibuja la gráfica sin reiniciarla
        3. Programa próxima actualización
        """
        if not self._refrescando:
            return
            
        # Obtiene copia segura de los datos
        with self.data_lock:
            x_data = self.x_data[-self.max_datos:]
            y_data = self.y_data[-self.max_datos:]
            
            x1_data = self.x1_data[-self.max_datos:]
            y1_data = self.y1_data[-self.max_datos:]
            
            x2_data = self.x2_data[-self.max_datos:]
            y2_data = self.y2_data[-self.max_datos:]
            
            

        
        # Actualización gráfica si hay nuevos datos
        if x_data and y_data and x1_data and y1_data and x2_data and y2_data:
            self.ax.clear()
            self.ax.plot(x_data, y_data, 'r-', label='Señal')
            self.ax.set_title("Señal en Tiempo Real")
            self.ax.set_xlabel("Tiempo (s)")
            self.ax.set_ylabel("Amplitud")
            self.ax.legend()
            self.canvas.draw()
            
            
            
            self.ax1.clear()
            self.ax1.plot(self.x1_data, self.y1_data, color='blue', label='RAM Total')
            self.ax1.set_title("Uso de RAM")
            self.ax1.set_xlabel("Tiempo")
            self.ax1.set_ylabel("RAM (MB)")
            self.ax1.legend()
            self.canvas1.draw()
            
            
            self.ax2.clear()
            self.ax2.plot(self.x2_data, self.y2_data, color='green', label='CPU Total')
            self.ax2.set_title("Uso de CPU")
            self.ax2.set_xlabel("Tiempo")
            self.ax2.set_ylabel("CPU (%)")
            self.ax2.legend()
            self.canvas2.draw()
            
        # Programa próxima actualización (50ms)
        self.after(50, self._actualizar_grafica)

    def stop_monitor(self):
        """
        Detiene limpiamente el monitoreo:
        1. Detiene hilo de recepción
        2. Cierra socket
        3. Detiene actualización gráfica
        """
        self._refrescando = False
        self.recibiendo_datos = False
        
        if self.tcp_socket:
            try:
                # Envía comando de parada
                self.tcp_socket.sendall(json.dumps({"stop": True}).encode('utf-8'))
                self.tcp_socket.close()
            except Exception as e:
                print(f"[WARN] Error al cerrar conexión: {e}")
            finally:
                self.tcp_socket = None

    def run(self):
        """Inicia el bucle principal de la aplicación"""
        self.mainloop()

if __name__ == '__main__':
    app = AppWindow()
    app.run()