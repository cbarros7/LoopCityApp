## **Documentación del Proceso de Inicialización de un Replica Set de MongoDB con Docker Compose**

Este documento detalla el proceso de configuración y los desafíos enfrentados al inicializar un replica set de MongoDB (versión 6.0) utilizando Docker Compose, incluyendo la configuración de autenticación, la creación de un usuario de aplicación y la inicialización de colecciones e índices.


### **1. Arquitectura del Replica Set**

Se configuró un replica set de MongoDB con tres nodos (`mongodb1`, `mongodb2`, `mongodb3`) para asegurar alta disponibilidad y redundancia de datos. Los nodos se comunican dentro de una red Docker definida por Compose.

- **Servicios:**

  - `mongodb1`, `mongodb2`, `mongodb3`: Contenedores de MongoDB (`mongo:6.0`).

  - `mongodb-init`: Contenedor efímero para ejecutar scripts de inicialización post-despliegue.

- **Volúmenes:** Volúmenes persistentes para cada nodo de MongoDB para asegurar la persistencia de los datos.

- **Red:** Una red Docker interna (`mongo-net`) para la comunicación entre los nodos.

- **Autenticación:** Habilitada mediante un **keyfile** compartido entre los nodos para la comunicación interna del replica set, y usuarios con credenciales para la autenticación externa.


### **2. Archivos de Configuración Clave**

- `.env`**:** Archivo de variables de entorno para gestionar credenciales de administrador, de aplicación y nombres de bases de datos.

- `docker-compose.yml`**:** Define los servicios, volúmenes, redes y la configuración de MongoDB, incluyendo el uso del keyfile y el mapa de puertos.

- `databases/mongo/mongo-keyfile`**:** El archivo secreto (con permisos `chmod 400`) para la autenticación interna del replica set.

- `databases/mongo/scripts/mongodb_init.sh`**:** Script Bash principal que orquesta la inicialización del replica set y la creación de usuarios/colecciones.

- `databases/mongo/scripts/init_replica_set.js`**:** Script JavaScript ejecutado por `mongodb_init.sh` para iniciar el replica set.

- `databases/mongo/scripts/create_app_user.js`**:** Script JavaScript ejecutado por `mongodb_init.sh` para crear el usuario de la aplicación, la base de datos y las colecciones/índices.


### **3. Proceso de Inicialización General**

El proceso sigue estos pasos orquestados por `mongodb_init.sh`:

1. **Espera a que** `mongodb1` **esté accesible:** Un bucle `until` que hace `ping` a `mongodb1` hasta que responde.

2. **Inicializa el Replica Set:** Ejecuta `init_replica_set.js` en `mongodb1`. Esto solo ocurre una vez.

3. **Espera la Elección del Primario:** Un bucle `until` más sofisticado que verifica explícitamente que `mongodb1` (o cualquier nodo al que se conecte) sea el `PRIMARY` del replica set.

4. **Crea el Usuario de Aplicación y Colecciones:** Ejecuta `create_app_user.js` en el nodo primario detectado, pasando las credenciales de la aplicación y el nombre de la base de datos.

5. **Reintenta la Creación (Bucle de Robustez):** Si la creación del usuario o las colecciones falla (comúnmente por `not primary`), el script reintenta la operación varias veces con un tiempo de espera entre intentos.


### **4. Desafíos y Soluciones Detalladas**

Durante el proceso, enfrentamos varios desafíos comunes en la configuración de replica sets en Docker:

***


#### **Challenge 1: Error** `MongoServerError: Authentication failed`

- **Síntoma:** El script `mongodb_init.sh` falla al conectarse a MongoDB con "Authentication failed" al intentar inicializar el replica set o crear usuarios.

- **Causa:**

  1. El **keyfile** no está siendo reconocido por los nodos de MongoDB.

  2. Los permisos del keyfile no son los correctos (`chmod 400`).

  3. El `docker-compose.yml` no está montando correctamente el keyfile en `/etc/mongo-keyfile`.

  4. Las variables de entorno `MONGO_ROOT_USERNAME` o `MONGO_ROOT_PASSWORD` en el `.env` o `docker-compose.yml` son incorrectas o no se están cargando.

  5. Se intentó autenticar con un usuario que aún no existía.

- **Solución:**

  1. Asegurar que el **keyfile se genere correctamente**: `openssl rand -base64 75 > ./databases/mongo/mongo-keyfile`.

  2. Establecer los **permisos correctos**: `chmod 400 ./databases/mongo/mongo-keyfile`.

  3. Verificar la **montura del volumen** en `docker-compose.yml` (`volumes: - ./databases/mongo/mongo-keyfile:/etc/mongo-keyfile`).

  4. Asegurar que la configuración de los nodos MongoDB en `docker-compose.yml` incluya la **autenticación** (`command: ["mongod", ..., "--keyFile", "/etc/mongo-keyfile"]`).

  5. Verificar que las **variables de entorno de root** (`MONGO_ROOT_USERNAME`, `MONGO_ROOT_PASSWORD`) estén correctamente definidas en `.env` y referenciadas en `docker-compose.yml`.

  6. **Conectarse con el usuario** `admin` **a la base de datos** `admin` para operaciones iniciales y de administración, ya que es el único usuario disponible antes de crear otros.

***


#### **Challenge 2: Error** `MongoServerError: not yet initialized`

- **Síntoma:** El script `mongodb_init.sh` falla al intentar ejecutar `rs.initiate()` con "not yet initialized".

- **Causa:** El script `mongodb_init.sh` intenta inicializar el replica set demasiado pronto, antes de que los procesos `mongod` en todos los nodos estén completamente operativos y listos para la comunicación del replica set.

- **Solución:**

  1. Implementar un **bucle de espera robusto** al inicio de `mongodb_init.sh` para asegurar que el primer nodo de MongoDB (`mongodb1`) responda a un comando `ping` antes de intentar `rs.initiate()`.

  2. Usar `|| true` después de la llamada a `rs.initiate()` en el script `mongodb_init.sh` para permitir que el script continúe si el replica set ya ha sido inicializado en un intento anterior (lo cual generaría un error "already initialized" pero no es un problema).

***


#### **Challenge 3: Error** `MongoshInvalidInputError: [COMMON-10001] Invalid database name:` **o variables vacías**

- **Síntoma:** El script `create_app_user.js` informa que el nombre de la base de datos o el usuario de la aplicación son inválidos/vacíos, a pesar de estar definidos en `.env`.

- **Causa:** Las variables de entorno de Bash (`${VAR_NAME}`) no se interpolan correctamente en el argumento `--eval` de `mongosh` cuando se usan comillas simples anidadas o un escape incorrecto.

- **Solución:**

  1. Asegurar que la línea `--eval` en `mongodb_init.sh` utilice una **sintaxis de comillas doble-simple-doble** (`--eval "varName='"${VAR_VALUE}"';"`) para forzar a Bash a interpolar las variables correctamente dentro de la cadena JavaScript.

  2. Verificar que las variables en el archivo `.env` no estén vacías y estén correctamente definidas.

  3. Confirmar que `docker-compose.yml` está pasando estas variables de entorno al servicio `mongodb-init` correctamente.

***


#### **Challenge 4: Persistente** `MongoServerError: not primary` **durante la creación del usuario/colecciones**

- **Síntoma:** A pesar de que el replica set parece inicializado y las variables son correctas, el script `create_app_user.js` falla repetidamente con "not primary" al intentar operaciones de escritura.

- **Causa:**

  1. **Inestabilidad del Replica Set:** El nodo primario es elegido, pero luego rápidamente se baja o hay una reelección justo cuando el script intenta escribir. Esto es común en entornos con recursos limitados o alta latencia.

  2. **Conexión a un Secundario:** Aunque `mongodb1` es el destino inicial, otro nodo puede haber sido elegido como primario, y el script está intentando escribir en un secundario.

- **Solución:**

  1. **Esperar explícitamente al Primario:** Añadir un bucle `until` más sofisticado en `mongodb_init.sh` que no solo verifique la conectividad, sino que también confirme que el nodo al que se conecta (`mongodb1`) es el `PRIMARY` (o que un primario existe) utilizando `rs.status()` y `rs.isMaster().ismaster` (o `hello`).

  2. **Aumentar** `sleep`**:** Dar más tiempo (ej. 15-30 segundos) después de `rs.initiate()` y después de la detección del primario para que el replica set se estabilice completamente antes de intentar operaciones de escritura.

  3. **Implementar Bucle de Reintento para Operaciones de Escritura:** Envolver la ejecución de `create_app_user.js` en un bucle `while` en `mongodb_init.sh` que reintente la operación varias veces si falla, con un `sleep` entre intentos (ej., 5-10 segundos). Esto mitiga problemas transitorios de "not primary".

  4. **Asignar más Recursos a Docker:** Asegurar que Docker Desktop (o la máquina anfitriona) tenga suficientes CPUs y RAM asignadas para soportar la carga de un replica set de 3 nodos de MongoDB (mínimo 4 CPUs, 8GB RAM si es posible). La falta de recursos es una causa frecuente de inestabilidad del replica set.

***


### **Conclusión**

A través de estos pasos y soluciones, hemos logrado configurar un replica set de MongoDB robusto y funcional dentro de Docker Compose, manejando los desafíos comunes de inicialización y autenticación. La clave reside en la **paciencia en las esperas**, la **correcta gestión de las variables de entorno** y la **robustez del script de inicialización** para manejar las condiciones de carrera inherentes a los sistemas distribuidos.
