# Information Transfer Protocol (ITP)
El Protocolo de Transferencia de Información o ITP es un protocolo de aplicación creado para hacer la transferencia de archivos y comandos con un host remoto. Este protocolo es capaz de enviar información grande como archivos de cualquier tipo, también es capaz de ejecutar comandos remotos para agilizar algunas tareas. Este protocolo requiere de una autenticación para poder establecer correctamente la conexión entre máquinas. Para este protocolo no se ha usado librerias externas y se ha trabajado con las nativas de python.

A continuación se presenta la [especificación de ITP](SPECIFICATION.md) para que pueda leer a profundidad como se implementa este protocolo

## Auntenticación
Como ya se ha mencionado, este protocola necesita una antenticación del cliente hacia el servidor o el host remoto, esta es una autenticación básica por usuario y contraseña. El servidor se encarga de leer los datos enviados y comparar esos datos con los almacenados en un archivo de texto (txt) que simula una Base de Datos. Se está de acuerdo que esta autenticación es muy debil y es suceptible a ser vulnerada pero por cosas practicas se ha mantenido para esta versión inicial del protocolo.

### Cómo autenticarse.
Para autenticarse primero debe ejecutar el comando `auth`. Solo ingrese la palabra `auth` despues de haber hecho la conexión. Luego se le pedirá que ingres su usuario y contraseña separados por comas de tal forma:
```log
>> auth
>> Ingrese el nombre de usuario y contraseña: username,password
```
Luego de esto el servidor validará los datos y en caso de ser correctos enviará `auth|A1` De lo contrario se enviará `Not authentication` y se cerrrará la conexión.

## Uso
El uso de este protcolo es bastante simple, primero se debe de separar los scripts, el `server.py` debe de estar en la maquina que se desea utilizar como servidor o host remoto, en tal script lo que debe de cambiarse es la forma de conexión en la llamada de la función `main` (dentro del `if __name__ == "__main__"`) en la llamada de la función se debe de cambiar el primer parámetro por su dirección ipv4 y el segundo parámetro indica el puerto. Una vez configurado esos 2 parámetros se procede a la ejecución del script y queda a la escucha de conexiones.

Para el cleinte no se debe de hacer configuración alguna ya que los datos del host son proporcionados por un input, se le pide la ip del host remoto y el puerto y debe ser ingresado de tal forma `ip_host,port` por ejemlo `192.168.0.103,82` y entonces se procede a la conexión y si todo va bien verá una entra de datos como shell `>>>` donde deberá de introducir el susuario y contraseña separados por una coma `>>> username,password` 

## Transferencia de Información
Para la transferencia de información existen 3 sencillos comandos 2 de ellos es para tratar con archivos y el otro es para usar comandos.

- `-file <filename>` : Este comando se usa cuando se quiere enviar información del cliente al servidor, el prefijo `-file` indica que será un archivo y `filename` es el nombre del archivo y el servidor guardará el archivo con el mismo nombre. El cliente envía una cabecera con la información para preparar al servidor y luego de esto se envía el contenido del archivo. Para el caso en que el archivo sea de un tamaño mayor a 1024 bytes se divide y se envía la información por bloques. Posterior se procede al envio por bloques del archivo. Para este momento el servidor ya se ha preparado para la lectura de cada bloque del archivo, donde se recibirá cada bloque y luego será juntado y creado el archivo.

- `-get-file <filename>` : Este comando es usado cuando se quiere pedir un archivo del servidor hacia el cliente. El servidor se encarga de buscar el archivo y en caso de no existor devuelve un `Not Found Error` pero la conexión no se cierra. En caso exista el archivo se procede a hacer los mismos pasos que cuando se envía archivos del cliente al servidor, primero se envía una cabecera `-size <num_blocks>` donde `-size` le indica al clienten que se recibirá un archivo por bloques y `num_blocks` es el número de bloques entonces el servidor procede a particionar el archivo y enviar los bloques.

Toda la operación entre archivos se hace de forma binaria par evitar problemas con la codificaión de algún archivo. También cabe resalatar que la información no va codificada pero, como ya se ha mencionado, esto es por fines practicos y será corregido en la siguiente versión del protocolo. La transferencia de archivos funciona con cualquier tipo de archivo desde `.txt` hasta `.py`

- `-cmd <command>` :  Este comando se utiliza cuando se quiere ejecutar un comando de forma remota en el servidor o host remoto. El prefijo `-cmd` le indica al servidor que se trata de un comando que será ejecutado y su respuesta será enviada. Los errores tambien son manejados y enviados al cliente en caso de existir. Si el comando no tiene una respuesta de retorno entonces el cliente se queda a la espera interminable de una respuesta, esto se ha visto al ejecutar el comando `-cmd python` para inicializar el intérprete de Python en modo interactivo donde claramente al ejecutar `python` en una terminal no hay respuesta alguna y se inicializa el intérprete.

## Carcterísticas
- En caso se envie algun mensaje que no sea un comando válido siempre se devolverá un `sts:|A1`.

- Para la codificación de números para enviar el tamaño de un archivo se utiliza el orden de bytes `little-endian`.

- Los mensajes se envian codificados como bytes, en caso el servidor no pueda interpretar o decodificar correctamente el mensaje enviado devuelve un mensaje de error `error|No se puedo decodificar el mensaje`.

- No existe un archivo `requirements.txt` ya que no se ha usado ningún módulo externo, todos los módulos usados ya vienen instalados por defecto en Python 3.x

## Notas

Para usar este protcolo en su forma "cruda" (como script de python) se debe de usar una versión de Python 3.5 o posterior, esto debido al uso de "Sugerencias de tipo" especificado en el  [PEP484](https://www.python.org/dev/peps/pep-0484/), si desea puede usar cualquier versión de Python 3.x pero deberá quitar todas las sugerencias de tipo añadidas en el código, esto ha sido añadido con el fin de que otras personas que contribuyan con el código tengan una noción de como funcionan algunas cosas del código.