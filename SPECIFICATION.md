# Especificación de ITP (Information Transfer Protocol)

ITP o Information Transfer Protocol es un protocolo simple diseñado para la transferencia de información de forma bidireccional, ya sea archivos o texto plano de una forma sencilla, simplificada y eficiente. Con este protocolo se espera proveer una forma rápida y sencilla para la transferencia de información en aplicaciones pequeñas o medianas. El punto débil de este protocolo es la seguridad del mismo. La autentición no es la mejor y no se hace comprobación y no existe restricción alguna sobre los comandos ejecutables en el shell.

## <a name="formato_de_datos"></a>Formato de datos
ITP usa un formato de encabezado de 18 bytes para cada segmento de datos transmitidos. Una solocitud se compone de los siguientes campo:

|   Campo   |       Descripcion             | Nro. bytes   |
|-----------|-------------------------------|--------------|
| longitud  |longitud del contenido a enviar|  12 bytes    |
|   comando |comando o acción a ejecutar    |  5 bytes     |
|   datos   |datos a enviar al cliente      |  variable    |

Los 2 primeros items corresponde al header o encabezado, hasta donde se ve son 17 bytes, se añade 1 byte para la separación (`|`) de la información en el encabezado. La longitud hace referencia a la longitud de los datos, sin considerar al comando. La estructura del encabezado es la sigueinte
```
<longitud>|<comando>
```

**Estructura de la solicitud**
```
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           <longitud>          |           <comando>           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               :
   :                            <Datos>                            :
   :                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
Todo el resto de información que esté seguida de este encabezado se considera como datos o contenido de la solicitud. Este no necesita ningún formato particular si solo se quiere enviar información (**no para la ejecución de comandos remotos**).

## Codificación
Para la longitud en el header esta debe estar especificada en bytes, con un orden de bytes de `little-endian`. El servidor hace la conversión de bytes a entero.

Para el comando y los datos estos también deben ser bytes pero en formato `utf-8`. El servidor hará la decodificaión correspondiente en `utf-8`.

## <a name="reglas_de_comunicacion"></a>Reglas de comunicación
Para poder establecer una comunicación con el servidor el cliente debe enviar como primera solicitud una autenticación (ver [Autenticación y seguridad](#autenticacion_y_seguridad)). Una vez confirmada la autenticación se procede a la trnasmisión del flujo de datos de manera normal.
Existe la posibilidad de que el servidor no retorne respuesta alguna y es correcto. No todos los comandos retornarán una respuesta, en caso lo desee se puede enviar un byte nulo como respuesta.

## <a name="autenticacion_y_seguridad"></a>Autenticación y seguridad
En el encabezado se debe especificar `auth` como comando, seguido del usuario y contraseña en formato `usuario,password`. Ejemplo
```
\x10\x00\x00\x00\x00\x00\x00\x00|auth\x00\x00\x00\x00\x00usuario,password
```
Luego de ser autenticado ya se procede a la transferencia de información. Para evitar posibles errores al enviar una solicutd entera se recomienda añadir bytes de relleno (bytes nulos) para completar los 18 bytes de encabezado, seguido de un salto de linea y los datos de la solicitud.

## <a name="intercambio_de_info"></a>Intercambio de información
Para el intercambio de información entre cliente y servidor existe los comando. Para la ejecución de comandos se debe enviar adicionalmente los argumentos con que será ejecutado el comando. **En caso no exista argumentos el contenido de la solicitud actúa como  argumento (único argumento para el comando)**.

**Varios argumentos:**  
En caso se requiera enviar más de 1 argumento la estructrua del contenido de la solicitud debe de tener los argumentos en formato `arg1 arg2 argn` (separados por espacios). La longitud máxima para el envio de argumentos es de 256 bytes (considerando los espacios). En caso de no alcanzar la longitud máxima se debe de rellenar con bytes nulos o vacíos (`\0`)

### Estructura de la solicitud
```
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           <longitud>          |           <comando>           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |              args             |          <argumentos>         | # se puede ignorar si no hay argumentos
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               :
   :                            <Datos>                            :
   :                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
### Descripción de la lectura o interpretación de la solicitud
Despues de haber leido e interpretado el header (longitud y comando) se procede a una lectura de reconocimiento, donde se leen los primeros 5 bytes siguientes, si estos bytes son coincidentes con la cadena `args|` significa que se estan enviando argumentos y se procede a la lectura de los siguientes 256 bytes. El resto de información es el contenido de la solicitud y se sigue leyendo según lo establecido en el header.
En caso los 5 bytes de reconomiento no sean coincidentes se continua con la lectura del contenido de la solicitud según lo establecido en el header pero sin considerar los 5 bytes iniciales, es decir se leerá `<longitud> - 5` bytes y al finalizar se tendrá que guntar los 5 bytes de reconocimiento iniciales con el resto del contenido leido.

### Comandos básicos
Los comandos implementados y básicos por defecto deben ser los siguientes:

1. `-file`: Envia un archivo del cliente al servidor, en otras palabras crea un archivo en el servidor.
    - Comando: `-file`
    - Argumentos:
        - Nombre del archivo (considerando la extensión)
    - Datos:  
        - Contenido del archivo

2. `-gfile`: Este comando especifica que se está solicitando un archivo al servidor.
    - Comando: `-gfile`
    - Argumenntos:
        - nombre del archivo solicitado
3. `-cmd`: Este comando especifica que se ejecutará un comando de shell en el servidor.
    - Comando: `-cmd`
    - Argumentos:
        - Comando a ejecutar en shell (depende del S.O. donde se ejecuta)

4. `close`: Este comando cierra la conexión entre ambas partes
    - Comando: `close`
    - Argumentos: No tiene argumentos

Para la transmisión de datos "de forma cruda". Es decir al llegar al servidor este lo puede procesar de la forma en que le sea conveniente. 
Se debe especificar `txt` como comando, esto indica que se está enviando un texto plano, el servidor hara un procesamiento separado de este mensaje. No ejecuta ninguna acción por defecto en el servidor. Es como un envio normal de datos. El usuario debe hacer una implementación propia para este comando.

### Importante
Para los errores se especifica el comando `error` no debe usar este comando como forma de transmición, solo para dar a conocer que ocurrió un error. Ver apartado de [Errores](#errores) para más información.

### Respuestas

**Nota:** Si la respuesta es otro comando a ejecutar no deberá seguir este formato. En cambio debe seguir con el formato normal para el envio de comandos. Este formato de respuesta solo es válido si la respuesta _**no**_ es otro comando remoto.

Toda petición debe enviar una respuesta. Esta respuesta debe tener en primera instancia una cabecera en formato:
```
<longitud_de_la_respuesta>|<codigo_de_respuesta>
```
La cabecera cabecera debe contener el tamaño del contenido de la respuesta (en caso exista) seguido de una barra y el código de respuesta.  

En caso no exista respuesta por alguna de las partes (cliente o servidor) de todas formas se envia una cabecera, pero indicando `0` como longitud y como código de respuesta se usa `A1`.  

En caso todo haya ido de forma nominal. El cliente (o la parte que está pendiente de la respuesta) siempre deberá de leer los datos de la otra parte, **no hay forma de que se envie una solicitud y luego de eso no haga una lectura de datos, siempre se deberá hacer una lectura de datos**. En caso se encuentre como código de respuesta una cadena `error` significa que ha ocurrido un error y se debe continuar con la lectura de datos según la longitud dada para obtener el código de error y el mensaje de error para notificar al usuario de la forma en que sea conveniente. Ver apartado de [Errores](#errores) para más información del retorno de errores.  

Si la longitud es `0` significa que no hay respuesta por parte del servidor (se debe especificar también `A1` como código de respeusta)

Para el caso de que una respuesta tenga datos la cabecera enviada debe estar en el siguiente formato:
```
<longitud_de_la_respuesta>|A2
```
Nuevamente la longitud de la respuesta debe estar en bytes en un orden de bytes `little-endian`. El `A2` es el código de respuesta. Puede ver todos los códigos de respuesta válidos en el apartado de [Códigos de respuesta](#cod_resp).


## <a name="errores"></a>Errores
Al ocurrir un error en el servidor este puede retornar varios tipo de errores. El formato al enviar un error es parecido a una solicitud normal. Solo se añade el codigo de error y un mensaje de error. A continuación se muestra un ejemplo de la respuesta completa que debe ser enviada por el servidor o la parte que responda.

**Ejemplo**
```
<longitud>|error <codigo_de_error>:<mensaje_de_error>
```

### Estructura de la respuesta
```
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |            <longitud>         |             error             |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               :
   :              <codigo_de_error>:<mensaje_de_error>             :
   :                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```


## <a name="cod_resp"></a>Códigos de respuesta

- ### Respuesta Satisfactoria `A1`
    El código para indicar una respuesta satisfactoria es `A1`. Esto indica que no hay data que envie el servidor y que todo fue con normalidad.

- ### Respuesta Satisfactoria con datos de retorno `A2`
    El código `A2` indica que la respuesta es satisfactoria y que hay datos que se están retornando y deben ser leídos.

- ### Respuesta Fallida `S0`
    El código `S0` indica una respuesta fallida, que ha ocurrido un error en el servidor, puede ser cualquier error.

- ### Error en header `H0`
    El código `H0` indica que el header que se ha enviado no está en el formato específico. El servidor no lo puede interpretar.

- ### Error en shell `C13`
    El código para indicar que ha ocurrido un error al momento de ejecutar algún comando en una shell se usa el código de respuesta `C13`.

- ### Error en el comando `C0`
    El Código `C0` indica que ha ocurrido un error durante la ejecución de algún comando distinto a `txt`.

- ### Error al eliminar archivos `707`
    El código `707` indica que no se ha podido eliminar algún archivo en el cliente o servidor. En un futuro relacionado con el comando `dfile`

- ### Error al enviar archivo `719`
    El código `719` indica que no se ha podido enviar algún archivo. Esto con el comando `file` o `gfile`.