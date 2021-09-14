from socket import socket
from os import path, getcwd, system
from time import sleep

ip,port = input("Ingrese el host y el puerto <host,port>: ").split(",")
sock = socket()
sock.connect((ip,int(port)))

def get_file(filename:str, content:bytes, sock:socket=None, blocks=None)->bool:
    ruta = path.join(getcwd(), "files", filename)

    if blocks:
        content = b""
        while True:
            res = sock.recv(1024)
            if res == b"complete":
                print(res.decode())
                break
            content+=res
    with open(ruta,"wb") as f:
        f.write(content)

def send_file(filename:str, sock:socket)->bytes:
    try:
        ruta = path.join(getcwd(),"files", filename)
        size = path.getsize(ruta)
    except Exception as e: 
        return f"{e}".encode()

    with open(ruta,"rb") as f:
        cont = f.read()
    if size>1024:
        sock.sendall(f"-file -size {(size//1024)+1} {name}".encode())
        for i in range(0, size, 1024):
            content = cont[i: i+1024]
            sock.sendall(content)
            sleep(0.7)        
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
    else: 
        msg = msg if type(msg) is bytes else msg.encode()
        sock.send(msg)
        res = sock.recv(1024)

    if b"-size " in res: 
        blocks = int(res.decode().split("-size ")[1])
        name = msg.decode().split("-get-file ")[1]
        get_file(name, res, sock, blocks=blocks)
    elif res == b"-file":
        #print(res, msg)
        name = msg.decode().split("-get-file ")[1]
        res = sock.recv(1024)
        get_file(name, res)
        print(sock.recv(1024).decode())
    else:
        print(res.decode())

sock.close()
print("Conexion cerrada")