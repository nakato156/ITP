from socket import socket
from subprocess import Popen, PIPE
from os import getcwd
from os.path import getsize, join

HEADER_BYTES = 18

def files(con:socket, length:int, *args)->bytes:
    filename = args[0]
    content = b""
    
    if length > 1024:
        num_bytes = length
        my_bytes = 0
        while my_bytes != num_bytes:
            res = con.recv(1024)
            my_bytes+=len(res)
            content+= res
        print("terminate")
    else:
        content = con.recv(1024)

    path = join(getcwd(),"files",filename)    
    with open(path, "wb") as f:
        f.write(content)

def get_file(con:socket, length:int, name:str)->bytes:
    try:
        path = join(getcwd(),"files",name)
        size = getsize(path) 
        with open(path,"rb") as f:
            file = f.read()
        if size>1024:
            con.sendall(f"-size {size}".encode())
            for i in range(0, size, 1024):                
                content = file[i:i+1024]               
                con.sendall(content)
        else:
            con.sendall(file)
    except Exception as e:
        return f"Error: {e}".encode()            

def cmd(sock: socket, *args)->bytes:
    cmd = args[1]
    try:
        process =Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr =process.communicate()
        res = stdout if stdout else stderr
        sock.sendall(f"-size {len(res)}".encode())
        if len(res) < 1024:
            sock.sendall(res)
        else:
            for i in range(0, len(res), 1024):
                sock.sendall(res[i: i * 1024])
    except FileNotFoundError as e:
        print(e)
        return f"{e}".encode()    

def authenticate(user:str, pwd:str)->bool:
    with open(".db.txt") as f:
        usernames, passwords = [[ln.strip().split(",") for ln in line.split("=")[1:]] for line in f.readlines()]
        
    if (user,pwd) not in zip(*usernames,*passwords): 
        return False 
    return True

def make_error(sock:socket, msg:str, cod:int)->bytes:
    msg = f"error|{msg}:{cod}".encode()
    sock.sendall(msg)
    sock.close()
    exit()

def crear_header(longitud:int, comando:str):
    longitud = min(longitud, 10**12 - 1)

    longitud_bytes = longitud.to_bytes(8, byteorder='little')
    comando_bytes = comando.encode('utf-8')

    header = longitud_bytes + b'|' + comando_bytes
    header = header.ljust(HEADER_BYTES, b'\0')

    return header

def send_data(sock:socket, operacion:str, data:bytes):
    lenght = len(data)
    header:bytes = crear_header(lenght, operacion)
    sock.sendall(header + data)

def parse_header(sock:socket)->tuple:
    """
    ## Returns
    comando: str
        - Comando a ejecutar

    longitud: int
        - Longitud del contenido  
    """
    header:bytes = sock.recv(HEADER_BYTES)
    if not header:
        return None, None
    if not b"|" in header:
        make_error(sock, "header mal formado", 1)
    longitud_bytes, comando_bytes = header.split(b"|")
    longitud = int.from_bytes(longitud_bytes, byteorder='little')
    comando = comando_bytes.rstrip(b"\0").decode('utf-8')
    return comando, longitud

def parse_content(sock:socket, lenght:int) -> bytes:
    data = b''
    while len(data) < lenght:
        chunk = sock.recv(lenght + 1 - len(data))
        if not chunk: break
        data += chunk
    return data

def read_data(sock:socket) -> tuple:
    """
    ## Returns
    comando: str
        - Comando a ejecutar

    data: bytes
        - Contenido del mensaje recibido 
    """
    operation, lenght =  parse_header(sock)
    if not lenght: return None, None
    return operation, parse_content(sock, int(lenght))

functions = {
    '-file': files,
    '-gfile': get_file,
    '-cmd': cmd
}

def rec_data_serve(con:socket):
    while True:
        try:
            cmd,longitud = parse_header(con)
        except UnicodeError as e:
            print(e)
            con.sendall(b"error al momento de decodificar infromacion")
            continue    

        if not cmd: break
        elif cmd.startswith("-"): #if command exist
            args:list[str] = con.recv(1024).strip().decode().split(" ")
            verb = cmd
            functions[verb](con, longitud, *args)
            # send_data(con, f"r{verb}", res)
        else:
            send_data(con, "sts", b"A1")
            yield parse_content(con, longitud)

def server(host:str, port:int, callback=print):
    sock = socket()
    sock.bind((host,port))
    sock.listen(1)
    print("socket encendido")

    con,addr = sock.accept()
    print(f"conectado con {addr}")

    # pedir autenticacion
    cmd, length = parse_header(con)
    try:
        if cmd != "auth": raise ValueError("No se ha enviado una autenticacion")
        msg = parse_content(con, int(length)).decode()
        
        if not authenticate(*msg.split(",")): raise ValueError("aa")
    except ValueError as e:
        make_error(con, "not authenticate", 2)
    
    #autenticacion satisfactoria
    send_data(con, "auth", b"A1")

    while True:
        msg = next(rec_data_serve(con))
        if msg is None: break
        callback(msg)
    sock.close()

def main(host:str, port:int)->None:
    server(host, port)
    print("conexion cerrada")

if __name__ =="__main__":
    main("0.0.0.0", 82)
