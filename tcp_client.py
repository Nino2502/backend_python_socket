import socket

HOST = "127.0.0.1"
#Se conecta al servidor en la misma maquina

PORT = 8001
#Puerto donde se van a recibir los paquetes

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #socket.socket() crea un socket TCP
    
    s.connect((HOST, PORT))
    #Intenta conectarse al servidor
    
    print("Conectado al servidor TCP")
    #Solo este mensaje es para confirmar que se conecto con exito

    while True:
        data = s.recv(1024)
        #Recibe los datos del servidor(1024)
        #Maximo 1024 bytes por lectura.
         
        if not data:
        
            break
        #Si el servidor cierra la conexion, termina el bucle.
        
        print(data.decode('utf-8').strip())
        #decode('utf-8') convierte bytes a string
        #strip() elimina los espacios al principio al final.
        