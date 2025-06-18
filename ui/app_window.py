
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import socket
import json
import tkinter as tk
from ttkbootstrap import Style

class AppWindow(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title("Protocols WebSocket, TCP/IP, socket")
        self.geometry("1280x720")

        
        self.amplitud = 0
        
        
        self.hz = 0
        
        
        self.segundos = 0
        
        
        
        self.x_data, self.y_data, self.y1_data = [], [], []

        # Canvas + Scroll
        self.canvas_frame = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas_frame.yview)
        self.canvas_frame.configure(yscrollcommand=self.scrollbar.set)

        self.canvas_frame.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scroll_frame = ttk.Frame(self.canvas_frame)
        self.window_id = self.canvas_frame.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        
        
        def on_configure(event):
    # Ajustar ancho del frame interno al ancho del canvas para que el contenido no quede pegado
            self.canvas_frame.itemconfig(self.window_id, width=event.width)

        self.canvas_frame.bind("<Configure>", on_configure)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas_frame.configure(scrollregion=self.canvas_frame.bbox("all")))

        # Agregamos un frame interno con padding para centrar y dar márgenes al contenido
        self.inner_frame = ttk.Frame(self.scroll_frame, padding=(30, 10))
        self.inner_frame.pack(fill='both', expand=True)

        # UI ahora dentro del inner_frame con padding para evitar pegarse a la izquierda
        ttk.Label(self.inner_frame, text="Monitor TCP/IP", font=("Arial", 40), bootstyle='dark').pack(pady=10)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.inner_frame)
        self.canvas.get_tk_widget().pack(pady=10, fill='both', expand=True)  # expand para usar bien el espacio
        
        


        # Botón para iniciar monitoreo
        ttk.Button(self.scroll_frame, text="Iniciar monitoreo", bootstyle='dark', width=90, command=self.start_thread).pack(pady=10)

      
       # Entrada para cambiar amplitud
        ttk.Label(self.scroll_frame, text="Amplitud:").pack()
        self.entrada_amplitud = ttk.Entry(self.scroll_frame, width=20)
        self.entrada_amplitud.insert(0, str(self.amplitud))
        self.entrada_amplitud.pack()
        ttk.Button(self.scroll_frame, text="Actualizar Amplitud", bootstyle='secondary', width=40, command=self.actualizar_amplitud).pack(pady=10)


        # Entrada para cambiar Hz
        ttk.Label(self.scroll_frame, text="Hz").pack()
        self.entrada_hz = ttk.Entry(self.scroll_frame, width=20)
        self.entrada_hz.insert(0, str(self.hz))
        self.entrada_hz.pack()
        ttk.Button(self.scroll_frame, text="Actualizar Hz", bootstyle='warning', width=40, command=self.actualizar_hz).pack(pady=10)
        

        # Entrada para cambiar Segundos
        ttk.Label(self.scroll_frame, text="Segundos").pack()
        self.entrada_segundos = ttk.Entry(self.scroll_frame, width=20)
        self.entrada_segundos.insert(0, str(self.segundos))
        self.entrada_segundos.pack()
        ttk.Button(self.scroll_frame, text="Actualizar Segundos", bootstyle='danger', width=40, command=self.actualizar_seg).pack(pady=10)
        
        
        
        """
        
        ttk.Button(self.inner_frame, text="Enviar Configuración", bootstyle='success', width=40, command=self.enviar_configuracion).pack(pady=10)
        ttk.Button(self.inner_frame, text="Detener Monitoreo", bootstyle='danger', width=40, command=self.detener_monitoreo).pack(pady=10)
    
        """
    def actualizar_seg(self):
        try:
            nuevo_seg = float(self.entrada_segundos.get())
            
            self.segundos = nuevo_seg
            
            print(f"Soy los nuevos segundos por mandar . .{self.segundos}")
  
        except ValueError:
            print("Valor no valido :c ")
            
            
                
        
    def actualizar_hz(self):
        try:
            nuevo_hz = float(self.entrada_hz.get())
            
            self.hz = nuevo_hz
            
            print(f"Soy la nueva fuerza hz para actualizar . . {self.hz}")
        except ValueError:
            print("Valor no valido :c")   
        
        
        
    def actualizar_amplitud(self):
        
        print("Soy el cambio de variable . ", float(self.entrada_amplitud.get()))

        try:
            nueva_amplitud = float(self.entrada_amplitud.get())
            self.amplitud = nueva_amplitud
            print(f"Amplitud actualizada a: {self.amplitud}")
        except ValueError:
            print("Valor no válido para amplitud")

 
    def start_thread(self):
        t = threading.Thread(target=self.listen_tcp)
        t.daemon = True
        t.start()
        print(f"Iniciando monitoreo con amplitud: {self.amplitud}, con velocidad, {self.hz}, con un tiempo {self.segundos}")

    def listen_tcp(self):
        HOST = "127.0.0.1"
        PORT = 8001
        buffer = ""

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            config = {
                "amplitud" : self.amplitud,
                "hz" : self.hz,
                "segundos" : self.segundos
            }
            
            mensaje = json.dumps(config) + '\n'
            
            s.sendall(mensaje.encode('utf-8'))
            

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
                        y1 = paquete.get("cantidad_paquetes")  # Otra línea

                        if x is not None and y is not None:
                            self.x_data.append(x)
                            self.y_data.append(y)
                            self.y1_data.append(y1 if y1 is not None else y * 0.5)  # Valor alternativo si no hay y1

                            self.ax.clear()
                            self.ax.plot(self.x_data, self.y_data, color='red', label='y')
                            #self.ax.plot(self.x_data, self.y1_data, color='blue', linestyle='--', label='y1')
                            self.ax.set_title("Señales Recibidas")
                            self.ax.legend()
                            self.canvas.draw()

                        if paquete.get("fin"):
                            print("Se termino la tranmision jajajajajaj y eso que")
                            
                            return
                    except json.JSONDecodeError:
                        continue

    def run(self):
        self.mainloop()

if __name__ == '__main__':
    app = AppWindow()
    app.run()
