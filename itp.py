import typing as t
from os import getcwd
from os.path import join as osJoin, getsize

from socket import socket
from subprocess import Popen, PIPE

HEADER_BYTES = 18
ARGS_BYTES = 256

# colores
RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"

class ITP:
    def __init__(self, host:str = "0.0.0.0", port:int=31) -> None:
        self._sock = socket()
        self._con: socket = self._sock
        self._host = host
        self._port = port
        self._path_files = "files"
        
        self.FUNCTIONS = {
            '-file': self.send_file,
            'rfile': self._get_file,
            '-gfile': self.descargar_file,
            '-cmd': self._cmd,
            'close': self.close
        }
        self.builtint_func:set = set(self.FUNCTIONS.keys())
    
    def send_file(self, filename:bytes) -> None:
        filename_:str = filename.decode().strip()
        try:
            ruta = osJoin(getcwd(), self._path_files, filename_)
            size = getsize(ruta)
        except FileNotFoundError as e: 
            return self.enviar_error(f"{e}".encode(), "719")
        
        size_bytes = size.to_bytes(8, byteorder='little')
        args = self.empaquetar_args(filename, size_bytes)
        header = self.crear_header(size + len(filename) + len(args), "rfile")
        self._enviar_datos(self._con, header + args)

        print(f"{YELLOW}[+]\tenviando archivo...{RESET}")
        with open(ruta, "rb") as f:
            self._enviar_datos(self._con, f.read())
        print(f"{GREEN}[+]\tArchivo enviado{RESET}")
                         
    def _get_file(self, filename:t.Union[str, bytes], size:t.Union[int, bytes]):
        if type(size) == bytes:
            size = int.from_bytes(size, byteorder='little')
        if type(filename) == bytes:
            filename = filename.decode()
        filename = filename.strip()

        print(f"{YELLOW}[+]\tRecibiendo archivo...{RESET}")
        path = osJoin(getcwd(), self._path_files, filename)
        contenido = self._obtener_contenido(int(size))
        with open(path, "wb") as f:
            f.write(contenido)
        # sleep(10)
        print(f"{GREEN}[+]\tArchivo recibido{RESET}")

    def _cmd(self, cmd:bytes) -> None: 
        cmd = cmd.decode().strip()
        try:
            proceso = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = proceso.communicate()
            res = stdout if stdout else stderr
            if stderr:
                self.enviar_error(res.decode(), "c13")
            else:
                self._enviar_datos(self._con, self.crear_header(len(res), "A2") + res)
            proceso.kill()

        except Exception as e:
            self.enviar_error(str(e), "c13")

    def descargar_file(self, filename:t.Union[str, bytes]):
        self.exec_cmd("-file",filename.decode() if type(filename) == bytes else filename)
        self._con.sendall(self.crear_header(0, "A1"))

    def close(self):
        self._con.sendall(self.crear_header(0, "close"))
        self._con.close()
    
    def connect(self):
        self._sock.connect((self._host, self._port))
        return self

    def bind(self) -> tuple:
        """
        ## Returns
        addr: tuple (host, port)
        """
        self._sock.bind((self._host, self._port))
        self._sock.listen(1)
        self._con, addr = self._sock.accept()
        return addr
    
    def empaquetar_args(self, *args):
        return b"args|" + b" ".join(args).ljust(ARGS_BYTES, b'\0')

    def crear_header(self, longitud:int, comando:str):
        longitud = min(longitud, 10**12 - 1)

        longitud_bytes:bytes = longitud.to_bytes(8, byteorder='little')
        comando_bytes:bytes = comando.encode('utf-8')

        header:bytes = longitud_bytes + b'|' + comando_bytes
        header = header.ljust(HEADER_BYTES, b'\0')

        return header

    def _obtener_args(self, longitud:int) -> t.Tuple[bytes]:
        if longitud > ARGS_BYTES:
            cmd_args = self._con.recv(5)
            if cmd_args == b"args|":
                return self._con.recv(ARGS_BYTES).rstrip(b"\0").split(b" ")
            return (cmd_args + self._obtener_contenido(longitud - 5), )
        return (self._obtener_contenido(longitud), )
          
    def _obtener_header(self) -> t.Tuple[str, int]:
        """
        ## Returns
        comando: str
            - Comando a ejecutar

        longitud: int
            - Longitud del contenido  
        """
        header = self._con.recv(HEADER_BYTES)
        try:
            longitud_bytes, comando_bytes = header.split(b"|", 1)
            longitud = int.from_bytes(longitud_bytes, byteorder='little')
            comando = comando_bytes.rstrip(b"\0").decode('utf-8')
        except Exception as e:
            self._con.settimeout(2)
            try:
                while True:
                    data = not self._con.recv(1)
                    if not data:break
            except: pass
            self.enviar_error(str(e), "H0")
            return "", 0
        return comando, longitud
    
    def _enviar_datos(self, sock:socket, data:bytes):
        n = len(data)
        if n < 1024:
            sock.sendall(data)
        else:
            for i in range(0, n, 1024):
                sock.sendall(data[i: ( i + 1) * 1024])
    
    def _obtener_contenido(self, lenght:int) -> bytes:
        data = b''
        while len(data) < lenght:
            chunk = self._con.recv(lenght + 1 - len(data))
            if not chunk: break
            data += chunk
        return data

    def _parse_respuesta(self, data:bytes, cmd:str) -> t.Tuple[bytes, str, bool]:
        error = cmd == "error"
        if error:
            codigo, data = data.split(b":", 1)
            return data, codigo.decode(), error
        return data, cmd, error

    def _obtener_respuesta(self) -> t.Tuple[bytes, str, bool]:
        """
        Lee la respuesta de la otra parte luego de haber enviado una solicitud  
        ## Returns  
        data: bytes | None
            Informacion devuelta
        codigo: str
            Codigo de estado de la respuesta
        error: bool
            Indica si hay algún error
        """
        comando, longitud = self._obtener_header()
        data = self._obtener_contenido(longitud) if longitud > 0 else b""
        return self._parse_respuesta(data, comando)

    def enviar_error(self, msg_error:str, codigo:str):
        msg_error = f"{codigo}:{msg_error}"
        header = self.crear_header(len(msg_error), "error")
        self._con.sendall(header)
        self._enviar_datos(self._con, header + msg_error.encode())

    def enviar_solicitud(self, cmd:str, data:str) -> t.Union[bytes, None]:
        header = self.crear_header(len(data), cmd)
        self._enviar_datos(self._con, header + data.encode())

        cmd, longitud = self._obtener_header()
        args = self._obtener_args(longitud)
        codigo = cmd
        
        if len(args) == 1:
            res, codigo, error = self._parse_respuesta(args[0], cmd)
            if error:
                return f"{RED}Error [{codigo}]: {res.decode()}{RESET}".encode()
        if self.FUNCTIONS.get(codigo, None):
            if not self.FUNCTIONS[codigo](*args):
                res, codigo, error = self._obtener_respuesta()
        return res

    def exec_cmd(self, cmd:str, data:str) -> t.Union[bytes, None]:
        if cmd == "-file": return self.send_file(data.encode())
        if cmd == "close": return self.close()
        return self.enviar_solicitud(cmd, data)

    def enviar_msg(self, data:str) -> t.Union[bytes, None]:
        return self.enviar_solicitud("txt", data)

    def on(self, cmd:str):
        def wrapper(func):
            self.FUNCTIONS[cmd] = func
            return func
        return wrapper

    def run(self):
        while True:
            cmd, longitud = self._obtener_header()

            if not cmd or cmd == "close": break
            elif self.FUNCTIONS.get(cmd, None):
                res = self.FUNCTIONS[cmd](*self._obtener_args(longitud))
                if cmd in self.builtint_func: continue
                res = self.crear_header(len(res), "txt") + res if res else None
                self._enviar_datos(self._con, res or self.crear_header(0, "A1"))
        print(f"{GREEN}[+]\tSe ha cerrado la conexión{RESET}")
        self._sock.close()