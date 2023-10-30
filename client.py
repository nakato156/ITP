from socket import socket
from os import path, getcwd, system

ip,port = input("Ingrese el host y el puerto <host,port>: ").split(",")
sock = socket()
sock.connect((ip,int(port)))

HEADER_BYTES = 18

def crear_header(longitud:int, comando:str):
    longitud = min(longitud, 10**12 - 1)

    longitud_bytes = longitud.to_bytes(8, byteorder='little')
    comando_bytes = comando.encode('utf-8')

    header = longitud_bytes + b'|' + comando_bytes
    header = header.ljust(HEADER_BYTES, b'\0')

    return header

def get_file(filename:str, sock:socket)->bool:
    ruta = path.join(getcwd(), "files", filename)
    sock.sendall(crear_header(0, "-gfile") + filename.encode())

    header = sock.recv(1024)
    if b"-size " in header:
        content = b""
        num_bytes = int(header.decode().split("-size ")[1])
        
        my_bytes = 0
        while my_bytes<num_bytes: 
            res = sock.recv(1024) 
            my_bytes += len(res)
            content+=res
    else: content=header

    with open(ruta,"wb") as f:
        f.write(content)
    
    return b"complete"

def send_file(filename:str, sock:socket)->bytes:
    try:
        ruta = path.join(getcwd(),"files", filename)
        size = path.getsize(ruta)
    except Exception as e: 
        return f"{e}".encode()

    with open(ruta,"rb") as f:
        cont = f.read()
    
    header = crear_header(len(cont), "-file")
    print(header +  filename.encode())
    sock.sendall(header)
    sock.sendall(filename.encode())

    if size>1024:
        for i in range(0, size, 1024):
            content = cont[i: i+1024]
            sock.sendall(content)        
    else:
        sock.sendall(cont)

    return sock.recv(1024)

def exec_cmd(sock:socket, cmd:str)->bytes:
    sock.sendall(crear_header(len(cmd), "-cmd") + cmd.encode())
    header = sock.recv(1024)
    content = b""
    if b"-size " in header:
        longitud = int(header.decode().split("-size ")[1])
        while len(content)<longitud:
            content += sock.recv(1024)
    return content

def autenticacion(sock:socket, msg:str):
    msg = msg.encode("utf-8")
    data = crear_header(len(msg), "auth") + msg
    sock.sendall(data)

while True:
    msg = input(">>> ")
    if msg == "auth":
        autenticacion(sock, input("Ingrese el nombre de usuario y contraseña: "))
        res = sock.recv(1024)
        print(res.decode())
        continue
    if msg in ["exit","break"]:
        break
    elif msg in ["clear","cls"]:
        system("clear")
   
    if msg.startswith("-file "):
        name = msg.split("-file ")[1]
        res = send_file(name, sock)
    elif msg.startswith("-get-file "):
        name = msg.split("-get-file ")[1]
        res = get_file(name, sock)
    elif msg.startswith("-cmd"):
        cmd = msg.split("-cmd ")[1]
        res = exec_cmd(sock, cmd)
    else: 
        msg = msg if type(msg) is bytes else msg.encode()
        data = crear_header(len(msg), "txt") + msg
        sock.send(data)
        res = sock.recv(1024)

    print(res.decode())

sock.close()
print("Conexion cerrada")