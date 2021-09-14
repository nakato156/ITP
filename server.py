from socket import socket
from subprocess import Popen, PIPE
from time import sleep
from os import getcwd
from os.path import getsize, join

def files(con:socket = None, *args)->bytes: 
    args = args[0]
    filename = args[2] if "-size"==args[0] else args[0]
    content = b""
    if "-size" in args:
        for _ in range(int(args[1])):
            res = con.recv(1024)
            content+= res
        print("terminate")    
    else:
        content = con.recv(1024)

    path = join(getcwd(),"files",filename)    
    with open(path, "wb") as f:
        f.write(content)
    return b"create file"

def get_file(con:socket, name:str)->bytes:
    try:
        name = name[0]
        path = join(getcwd(),"files",name)
        size = getsize(path) 
        with open(path,"rb") as f:
            file = f.read()
        if size>1024:
            con.sendall(f"-size {size//1024}".encode())
            for i in range(0, size, 1024):                
                content = file[i:i+1024]               
                con.sendall(content)
                sleep(0.7)
        else:
            con.sendall(b"-file")
            sleep(0.5)
            con.sendall(file)   
        return b"complete"    
    except Exception as e:
        return f"Error: {e}".encode()            

def cmd(sock: socket, *args)->bytes:
    cmd = args[0]
    try:
        process =Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr =process.communicate()
        return (stdout if stdout else stderr)
    except FileNotFoundError as e:
        return f"{e}".encode()    

def authenticate(user:str, pwd:str)->bool:
    with open(".db.txt") as f:
        usernames, passwords = [[ln.strip().split(",") for ln in line.split("=")[1:]] for line in f.readlines()]
        
    if (user,pwd) not in zip(*usernames,*passwords): 
        return False 
    return True

functions = {
    '-file': files,
    '-get-file': get_file,
    '-cmd': cmd
}

def main():
    sock = socket()
    sock.bind(("192.168.0.105",82))
    sock.listen(1)
    print("socket encendido")

    con,addr = sock.accept()
    print(f"conectado con {addr}")

    msg = con.recv(1024).decode().strip()
    #authenticate
    try:
        if not authenticate(*msg.split(",")): raise
        else: con.sendall(b"auth:ok")
        global functions
    except:
        con.sendall(b"not authentication")
        con.close()
        exit()

    while True:
        try:
            msg = con.recv(1024).decode().strip()
        except Exception as e:
            print(e)
            con.sendall(b"error al momento de decodificar infromacion")
            continue    
        res = b"status:ok"
        if not msg: #verify close connection
            con.close()
            break
        if msg.startswith("-"): #if command exist
            #splitet headers
            headers = msg.split(" ")
            verb = headers[0]
            res = functions[verb](con, headers[1:])
        con.sendall(res)       
    sock.close()
    print("conexion cerrada")

if __name__ =="__main__":
    main()