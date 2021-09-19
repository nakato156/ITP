from socket import socket
from os import path, getcwd

ip,port = input("Ingrese el host y el puerto <host,port>: ").split(",")
sock = socket()
sock.connect((ip,int(port)))

def get_file(filename:str, sock:socket)->bool:
    ruta = path.join(getcwd(), "files", filename)
    sock.sendall(f"-get-file {filename}".encode())

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
    if size>1024:
        sock.sendall(f"-file -size {size} {name}".encode())
        for i in range(0, size, 1024):
            content = cont[i: i+1024]
            sock.sendall(content)        
    else:
        sock.sendall(f"-file {name}".encode())
        sock.sendall(cont)
    return sock.recv(1024)

while True:
    msg = input(">>> ")
    if msg in ["exit","break"]:
    	break
    elif msg in ["clear","cls"]:
        os.system("clear")
   
    if msg.startswith("-file "):
        name = msg.split("-file ")[1]
        res = send_file(name, sock)
    elif msg.startswith("-get-file "):
        name = msg.split("-get-file ")[1]
        res = get_file(name, sock)
    else: 
        msg = msg if type(msg) is bytes else msg.encode()
        sock.send(msg)
        res = sock.recv(1024)

    print(res.decode())

sock.close()
print("Conexion cerrada")