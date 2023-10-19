# Especificación de ITP (Information Transfer Protocol)

ITP o Information Transfer Protocol es un protocolo simple diseñado para la transferencia de información, ya sea archivos o texto plano de una forma sencilla, simplificada y eficiente. Con este protocolo se espera proveer una forma rápida y sencilla para la transferencia de información en aplicaciones pequeñas o medianas. El punto débil de este protocolo es la seguridad del mismo. La autentición no es la mejor y no se hace comprobación y no existe restricción alguna sobre los comandos ejecutables en el shell.

### <a name="formato_de_datos"></a>Formato de datos
ITP usa un formato de encabezado de 18 bytes para cada segmento de datos transmitidos. Una solocitud se compone de los siguientes campo:

|   Campo   |       Descripcion             | Nro. bytes   |
|-----------|-------------------------------|--------------|
| longitud  |longitud del contenido a enviar|  12 bytes    |
|   comando |comando o acción a ejecutar    |  5 bytes     |
|   datos   |datos a enviar al cliente      |  variable    |

Los 2 primeros items corresponde al header o encabezado, hasta donde se ve son 17 bytes, se añade 1 byte para la separación (`|`) de la información en el encabezado. La longitud hace referencia a la longitud de los datos, sin considerar al comando. La estructura del encabezado es la sigueinte
```
longitud|comando
```

**Estructura de la solicitud**
```
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |            longitud           |            comando            |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               :
   :                             Datos                             :
   :                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
Todo el resto de información que esté seguida de este encabezado se considera como datos o contenido de la solicitud.

### Codificación
Para la longitud en el header esta debe estar especificada en bytes, con un orden de bytes de `little-endian`. El servidor hace la conversión de bytes a entero.

Para el comando y los datos estos también deben ser bytes pero en formato `utf-8`. El servidor hará la decodificaión correspondiente en `utf-8`.

### <a name="reglas_de_comunicacion"></a>Reglas de comunicación
Para poder establecer una comunicación con el servidor el cliente debe enviar como primera solicitud una autenticación (ver [Autenticación y seguridad](#autenticacion_y_seguridad)). Una vez confirmada la autenticación se procede a la trnasmisión del flujo de datos de manera normal.

### <a name="autenticacion_y_seguridad"></a>Autenticación y seguridad
En el encabezado se debe especificar `auth` como comando, seguido del usuario y contraseña en formato `usuario,password`. Ejemplo
```
\x10\x00\x00\x00\x00\x00\x00\x00|auth\x00\x00\x00\x00\x00usuario,password
```
Luego de ser autenticado ya se procede a la transferencia de información. Para evitar posibles errores al enviar una solicutd entera se recomienda añadir bytes de relleno (bytes nulos) para completar los 18 bytes de encabezado, seguido de un salto de linea y los datos de la solicitud.

### <a name="intercambio_de_info"></a>Intercambio de información
Para el intercambio de información entre cliente y servidor existe los comando. Para la ejecución de comandos se debe enviar adicionalmente los argumentos con que será ejecutado el comando. Posteriormente del envio del header se debe hacer envio de los argumentos en formato `arg1 arg2 argn` (separados por espacios). La longitud máxima para el envio de argumentos es de 1024 bytes (considerando los espacios).

**Estructura de la solicitud**
```
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |            longitud           |            comando            |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                           argumentos                          |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               :
   :                             Datos                             :
   :                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Los comandos implementados y básicos por defecto deben ser los siguientes:

1. `-file`: Envia un archivo del cliente al servidor, en otras palabras crea un archivo en el servidor.
    - Comando: `-file`
    - Argumentos:
        - Nombre del archivo (considerando la extensión)
        - Contenido del archivo

2. `-gfile`: Este comando especifica que se está solicitando un archivo al servidor.
    - Comando: `-gfile`
    - Argumenntos:
        - nombre del archivo solicitado
3. `-cmd`: Este comando especifica que se ejecutará un comando de shell en el servidor.
    - Comando: `-cmd`
    - Argumentos:
        - Comando a ejecutar en shell (depende del S.O. donde se ejecuta el servidor)

Para la transmisión de datos "de forma cruda". Es decir al llegar al servidor este lo puede procesar de la forma en que le sea conveniente. 
Se debe especificar `txt` como comando, esto indica que se está enviando un texto plano, el servidor hara un procesamiento separado de este mensaje. No ejecuta ninguna acción en el servidor. Es como un envio normal de datos.

**Respuestas**
Toda petición debe enviar en primera instancia como cabecera el tamaño del contenido de la respuesta en caso existe, de lo contrario un byte nulo o vacío. Para el caso que exista una respuesta la cabecera enviada por el servidor debe estar en este formato:
```
-size longitud_de_la_respuesta
```
Nuevamente la longitud de la respuesta debe estar en bytes en un orden de bytes `little-endian`.

### Errores
Al ocurrir un error en el servidor este puede retornar varios tipo de errores. El formato al enviar un error es parecido a un encabezado normal. Solo se añade el codigo de error

**formato**
```
error|mensaje_de_error: codigo_de_error
```

Hasta el momento existe 2 tipos de respuestas. Una satisfactoria y otra fallida. Para la respuesta satisfactoria el código es `A1`. Para las repestas que indica un fallo o errores se utiliza el código `2`.
