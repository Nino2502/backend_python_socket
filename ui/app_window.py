import csv
#Para poder guardar los datos en un archivo CSV
import ttkbootstrap as ttk
# Para la interfaz gráfica y estilos
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
# Para la visualización de gráficos
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
#Para poder ejecutar diversos hilos
import socket
# Para manejar la conexión TCP
import json
#Para manejar la comunicación TCP y el formato JSON
import time
import tkinter as tk

# ================================ #
# Autor: Jesus Gonzalez Leal (Nino :3)
# Fecha: 26 de junio del 2025      
# Ultima modificacion: 30 de junio del 2025
# ================================ #

class AppWindow(ttk.Window):
    #Basicamnete el ttk.Window nos va ayudar a generar una ventana para poder visualizar las gráficas
    def __init__(self):
        super().__init__(themename="cyborg")
        self.title("Monitor TCP/IP - Realtime Signals")
        self.geometry("1280x720")
        #Aqui solo se asigna el titulo y el tamaño de la ventana

        # ============================== #
        #     VARIABLES DE CONFIGURACIÓN #
        # ============================== #
        
        #self.segundos = 15
        self.amplitud = 0      # Amplitud de la señal senoidal
        self.hz = 0            # Frecuencia de la señal en Hz
        self.max_datos = 30    # Máximo de puntos mostrados en gráfica
        self.data_lock = threading.Lock()  # Lock para seguridad en hilos
        self.historial_datos = []  # Almacena todos los datos recibidos
        self.segundos_ventana = 0 # Ventana de tiempo para visualizar la grafica
        
        # Buffers para datos gráficos
        #Basicamnete aqui se guardan los datos que se van a graficar
        #Que todos son ARRAYS
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
        #Aqui llamamos el metodo que contruye toda la interfaz grafica

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
        self.canvas.get_tk_widget().pack(pady=10)

        # ============================================= #
        #     PANEL DE CONTROL (PARÁMETROS)            #
        # ============================================= #
        controles_frame = ttk.Labelframe(self.inner_frame, 
                                       text="Configuración de Señal", 
                                       bootstyle="primary", 
                                       padding=15)
        controles_frame.pack(fill='x', pady=10)
        

        # Entrada para amplitud
        # Caja de entra de amplitud
        ttk.Label(controles_frame, text="Amplitud:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.entrada_amplitud = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 10))
        self.entrada_amplitud.insert(0, "10")
        self.entrada_amplitud.grid(row=0, column=1, sticky='ew', padx=5)

        # Entrada para frecuencia (Hz)
        # Caja de entra de frecuencia
        ttk.Label(controles_frame, text="Hz:", font=("Segoe UI", 12)).grid(row=0, column=3, sticky='e', padx=5)
        self.entrada_hz = ttk.Entry(controles_frame, width=10, font=("Segoe UI", 10))
        self.entrada_hz.insert(0, "10") 
        self.entrada_hz.grid(row=0, column=4, sticky='ew', padx=5)

        # Botón para iniciar/actualizar monitoreo
        ttk.Button(controles_frame, 
                 text="Iniciar/Actualizar Monitoreo", 
                 bootstyle='success outline', 
                 command=self.start_client).grid(row=0, column=9, padx=5, pady=5, sticky='ew', ipadx=20, ipady=10)

        # Botón para detener monitoreo
        ttk.Button(controles_frame, 
                 text="Detener Monitoreo", 
                 bootstyle='danger outline', 
                 command=self.stop_monitor).grid(row=0, column=10, padx=5, pady=5, sticky='ew', ipadx=20, ipady=10)
        
        control_grafica = ttk.Labelframe(self)
        
        # Responsive columns
        controles_frame.columnconfigure(1, weight=1)
        controles_frame.columnconfigure(4, weight=1)
        controles_frame.columnconfigure(9, weight=1)
        controles_frame.columnconfigure(10, weight=1)
        
        control_grafica = ttk.LabelFrame(self.inner_frame, text="Modificar Grafica", bootstyle= "primary", padding=15)
        control_grafica.pack(fill='x', pady=10)
        
        control_grafica.grid_columnconfigure(1, weight=1)
        control_grafica.grid_columnconfigure(4, weight=1)
        
        

        
        
        ttk.Button(control_grafica,
                   text="Modificar grafica",
                   bootstyle='danger outline',
                   command=self._ajustar_tamano_graficas).grid(row=0, column=1, padx=5, pady=5, sticky='ew', ipadx=20, ipady=10)
        
        ttk.Label(control_grafica, text="Change Size", font=("Segoe UI", 12)).grid(row=0, column=3, sticky='e', padx=5)
        
        self.tamano_graf = ttk.Entry(control_grafica, width=10, font=("Segoe UI", 10))
        self.tamano_graf.insert(0, self.segundos_ventana)
        self.tamano_graf.grid(row=0, column=4, sticky='ew', padx=5, ipadx=10, ipady=10)
        
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
        
    def _ajustar_tamano_graficas(self):
        tamano = self.tamano_graf.get().strip()

        # Validar si se ingresó algo
        if not tamano:
            messagebox.showerror("Error", "Debes ingresar un tamaño")
            return

        # Intentar convertir a entero
        try:
            tamano_init = int(tamano)
        except ValueError:
            messagebox.showerror("Error", "El tamaño debe ser un número entero")
            return

        # Validaciones del rango
        if tamano_init <= 0:
            messagebox.showerror("Error", "El tamaño debe ser mayor a 0")
            return
        if tamano_init > 60:
            messagebox.showerror("Advertencia", "El tamaño es muy grande y puede afectar el rendimiento")
            return

        self.segundos_ventana = tamano_init

        factor = 2
        ancho = max(4, tamano_init * factor)
        alto = 4

        self.fig.set_size_inches(ancho, alto, forward=True)

        dpi = self.fig.get_dpi()
        ancho_px = int(ancho * dpi)
        alto_px = int(alto * dpi)

        widget = self.canvas.get_tk_widget()
        widget.config(width=ancho_px, height=alto_px)

        self.canvas.draw()

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
            'cpu_percent','cpu_equipo_total','ram_percent','ram_total_equipo'
            #'vs_code_ram', 'cmd_exe_ram'
            ]
        
        
        try:
            with open(archivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

                for idx, row in enumerate(self.historial_datos, 1):
                    writer.writerow([
                        idx,
                        row["cantidad_paquetes"],
                        row["tiempo_transcurrido"],
                        row["hz"],
                        row["ts"],
                        row["cpu_process_percent"],
                        row["cpu_equipo_total"],
                        row["ram_process_mb"],
                        row["ram_equipo_total"],
                        #row["vs_code_ram"],
                        #row["cmd_exe_ram"]
                    ])
            messagebox.showinfo("Éxito", "Archivo CSV exportado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo CSV: {e}")

    def start_client(self):
        #Aqui en esta funcion van a ingresar las variables de la amplitud y la frecuencia
        
        try:
            # Aqui traemos la informacion de las entradas de amplitud y frecuencia strip() es para quitar los espacios en blanco
            # De al principio y al final de la cadena
            hz_input = self.entrada_hz.get().strip()
            amplitud_input = self.entrada_amplitud.get().strip()
            
            size_graph = self.segundos_ventana

            # Validamos que las entradas no esten vacias
            if amplitud_input != "":
                new_amplitud = float(amplitud_input)
                if new_amplitud > 0:
                    self.amplitud = new_amplitud
            
            # Validamos que la frecuencia no este vacia
            if hz_input != "":
                new_hz = float(hz_input)
                if new_hz > 0:
                    self.hz = new_hz
                    
            if size_graph is None or not isinstance(size_graph, int) or size_graph <= 0:
                messagebox.showerror("Error", "Por favor asigna un tamaño válido a la gráfica")
                return
                            
        except ValueError as e:
            messagebox.showerror("Error", f"Valor inválido: {e}")
            return

        # Mira aqui validamos que exista un objeto socket eso se valida en _iniciar_conexion()
        # Ah si asigna el socket a la variable tcp_socket no devuelve un True o False devuelve un objeto socket
        
        #Si no existe una object tcp_socket iniciamos la conexion
        if not self.tcp_socket:
            self._iniciar_conexion()
        else:
            #Si ya existe una conexion, simplemente enviamos los nuevos parametros
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
            #Aqui creamos el objeto socket
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            #aqUI con el object socket nos conectamos al servidor
            self.tcp_socket.connect(("127.0.0.1", 8001))
            
            # Envía parámetros iniciales
            self._enviar_parametros()
            
            # Inicia hilo para recepción de datos
            self.recibiendo_datos = True
            
            #Vamos a recibir datos de la conexion TCP
            threading.Thread(
                target=self.recibir_data, 
                args=(self.tcp_socket,), 
                daemon=True
            ).start()
            
            # Activa actualización gráfica si no estaba activa
            if not self._refrescando:
                self._refrescando = True
                self._actualizar_grafica()
                self._actualizar_grafica_ram_cpu()
                
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en conexión: {str(e)}")

    def _enviar_parametros(self):
        """Envía los parámetros actuales al servidor en formato JSON"""
        if self.tcp_socket:
            try:
                # Armas un mensaje JSON con los parámetros actuales
                msg = {
                    "amplitud": self.amplitud,
                    "hz": self.hz, 
                }
                
                # Como ya tenemos un objeto socket activo
                # Y simplemente enviamos el mensaje JSON al servidor con la funcion sendall
                self.tcp_socket.sendall((json.dumps(msg) + '\n').encode('utf-8'))
                
                # .encode('utf-8') convierte el string a bytes + \n para los saltos de línea
                
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
        hz_input = self.entrada_hz.get().strip()
        if hz_input != "":
            hz = float(hz_input)
            if hz > 0:
                self.hz = hz  # Actualiza la variable global
            else:
                raise ValueError("Hz debe ser mayor que 0")
        else:
            hz = self.hz  # Si está vacío, usamos el último valor válido

        ts = int((1 / hz) * 1000)
        
        if not self._refrescando:
            return
        
        tamano_ventana = int(self.segundos_ventana * hz)
    
        if tamano_ventana <= 0:
            tamano_ventana = 30  # Por defecto 30 puntos si no está bien configurado
        
        with self.data_lock:
            # Cortar a los últimos N datos para la ventana actual
            x = self.x_data[-tamano_ventana:]
            y = self.y_data[-tamano_ventana:]

            self.ax.clear()
            self.ax.plot(x, y, color="cyan", label="Señal Senoidal")
            self.ax.set_title(f"Señal senoidal con amplitud {self.amplitud} y frecuencia {self.hz} Hz")
            self.ax.set_xlabel("Tiempo (paquetes)")
            self.ax.set_ylabel("Amplitud")
            self.ax.grid(True, color="gray", linestyle="--", alpha=0.5)
            #self.ax.legend()

            self.canvas.draw()
            
            #Con el ts va a describir el tiempo que hay entre cada paquete::
            self.after(ts, self._actualizar_grafica)
            #WARNING is the code , because : Puede ocasionar cuello de botella

    def _actualizar_grafica_ram_cpu(self):
        """
        Actualización periódica de gráficas RAM y CPU:
        Similar a la principal, pero con dos gráficas independientes
        """
        if not self._refrescando:
            return
        
        hz_input = self.entrada_hz.get().strip()
        if hz_input != "":
            hz = float(hz_input)
            if hz > 0:
                self.hz = hz
            else:
                raise ValueError("Hz debe ser mayor que 0")
        else:
            hz = self.hz
        
        tamano_ventana = int(self.segundos_ventana * hz)
        if tamano_ventana <= 0:
            tamano_ventana = 30
        
        with self.data_lock:
            x1 = self.x1_data[-tamano_ventana:]
            y1 = self.y1_data[-tamano_ventana:]
            
            x2 = self.x2_data[-tamano_ventana:]
            y2 = self.y2_data[-tamano_ventana:]
        
            self.ax1.clear()
            self.ax1.plot(x1, y1, 'b-', label='RAM')
            self.ax1.set_title("Uso de RAM en Tiempo Real")
            self.ax1.set_xlabel("Tiempo (s)")
            self.ax1.set_ylabel("Uso RAM (MB)")
            #self.ax1.legend()
            
            self.ax2.clear()
            self.ax2.plot(x2, y2, 'g-', label='CPU')
            self.ax2.set_title("Uso de CPU en Tiempo Real")
            self.ax2.set_xlabel("Tiempo (s)")
            self.ax2.set_ylabel("Uso CPU (%)")
            #self.ax2.legend()

            self.canvas1.draw()
            self.canvas2.draw()

        self.after(5000, self._actualizar_grafica_ram_cpu)

    def stop_monitor(self):
        """
        Detiene la recepción de datos y cierra la conexión TCP.
        Resetea variables y buffers.
        """
        if self.tcp_socket:
            try:
                self.recibiendo_datos = False
                self._refrescando = False
                
                # Cierra el socket TCP
                self.tcp_socket.shutdown(socket.SHUT_RDWR)
                self.tcp_socket.close()
                self.tcp_socket = None
                
                # Limpia datos y buffers
                with self.data_lock:
                    self.x_data.clear()
                    self.y_data.clear()
                    self.x1_data.clear()
                    self.y1_data.clear()
                    self.x2_data.clear()
                    self.y2_data.clear()
                    #self.historial_datos.clear()
                
                # Limpia gráficas
                self.ax.clear()
                self.canvas.draw()
                self.ax1.clear()
                self.canvas1.draw()
                self.ax2.clear()
                self.canvas2.draw()
                
                messagebox.showinfo("Información", "Monitoreo detenido correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo detener el monitoreo: {e}")

if __name__ == "__main__":
    app = AppWindow()
    app.mainloop()
