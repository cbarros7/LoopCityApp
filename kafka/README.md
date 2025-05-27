Cómo Probar y Ejecutar

    Genera un KAFKA_CLUSTER_ID:
        Ejecuta un contenedor temporal de Kafka y usa su utilidad:
        Bash

    docker run --rm confluentinc/cp-kafka:7.5.0 kafka-storage random-uuid

    Copia el UUID generado y pégalo en el docker-compose.yaml (o en tu .env).

Crea el archivo .env: En la raíz de tu proyecto, con el contenido actualizado.

Instala Poetry y dependencias (localmente si vas a ejecutar scripts sin Docker):
Bash

pip install poetry
poetry install

Levanta el Clúster de Kafka con Docker Compose:
Bash

docker-compose up --build -d

    El kafka intentará formatear su almacenamiento (solo la primera vez) y luego iniciar.
    El kafka-topic-initializer esperará a que kafka esté healthy, luego ejecutará entrypoint.sh que a su vez llama a kafka_manager.py usando poetry run python.

Verifica los Topics:
Bash

docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

Deberías ver raw_events, raw_places, raw_weather.

Prueba el Productor (desde tu máquina local):
Bash

# Por defecto, el ambiente es 'development' del .env
poetry run python src/producer_example.py

# Para especificar un ambiente diferente (ej. si tuvieras "staging" local)
# poetry run python src/producer_example.py staging




## Para generar certificados 

# Navega a tu directorio certs/dev
cd kafka_project/certs/dev

# 1. Genera la clave privada del broker (cambia 'broker_key_password' por una clave segura)
openssl genrsa -des3 -passout pass:broker_key_password -out broker.key 2048

# 2. Genera una Solicitud de Firma de Certificado (CSR) para el broker
# El Common Name (CN) debe ser el hostname que tus clientes usarán para Kafka (ej. 'kafka' para la red interna de Docker)
openssl req -new -key broker.key -passin pass:broker_key_password -out broker.csr -subj "/CN=kafka"

# 3. Firma el CSR del broker con tu CA (cambia 'ca_key_password' por la clave de tu CA)
openssl x509 -req -days 365 -in broker.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out broker.pem -passin pass:ca_key_password

# Opcional: Elimina la contraseña de la clave privada del broker si lo prefieres para desarrollo (menos seguro)
# openssl rsa -in broker.key -passin pass:broker_key_password -out broker.key.nopass
# mv broker.key.nopass broker.key

----- 
 
 Convierte los certificados PEM a JKS/PKCS#12:
Kafka funciona bien con PKCS#12 (.p12) para las claves y certificados, y JKS (.jks) para los TrustStores.

# Asegúrate de estar en kafka_project/certs/dev

# 1. Crea el Keystore del Broker (contiene el certificado del broker y su clave privada)
# Reemplaza 'your_broker_keystore_password' por una contraseña segura
openssl pkcs12 -export -in broker.pem -inkey broker.key -passin pass:broker_key_password -name "broker" -out broker_keystore.p12 -passout pass:your_broker_keystore_password

# 2. Crea el Truststore del Broker (contiene el certificado de la CA raíz que firmó los certificados del cliente)
# Reemplaza 'your_broker_truststore_password' por una contraseña segura
keytool -import -file ca.pem -alias CARoot -keystore broker_truststore.jks -storepass your_broker_truststore_password -noprompt

# 3. Crea el Keystore del Cliente (contiene el certificado del cliente y su clave privada)
# Reemplaza 'your_client_keystore_password' por una contraseña segura
openssl pkcs12 -export -in client.pem -inkey client.key -passin pass:client_key_password -name "client" -out client_keystore.p12 -passout pass:your_client_keystore_password

# 4. Crea el Truststore del Cliente (contiene el certificado de la CA raíz que firmó los certificados del broker)
# Reemplaza 'your_client_truststore_password' por una contraseña segura
keytool -import -file ca.pem -alias CARoot -keystore client_truststore.jks -storepass your_client_truststore_password -noprompt

Paso 2: Actualizar .env con las nuevas Contraseñas

Añade las contraseñas que usaste para los keystores y truststores:

# .env
# ... (otras variables) ...

# Credenciales de Kafka SASL/SCRAM
KAFKA_USERNAME=loopcity_app_user
KAFKA_PASSWORD=secure_kafka_secret_password

# Credenciales para Keystores y Truststores Kafka SSL/TLS
KAFKA_BROKER_KEYSTORE_PASSWORD=your_broker_keystore_password
KAFKA_BROKER_TRUSTSTORE_PASSWORD=your_broker_truststore_password
KAFKA_CLIENT_KEYSTORE_PASSWORD=your_client_keystore_password
KAFKA_CLIENT_TRUSTSTORE_PASSWORD=your_client_truststore_password

------

Implicaciones para tu Configuración de Despliegue en Staging/Producción

Si decides que tus entornos de staging y production utilizarán SASL_PLAINTEXT, deberás asegurarte de que tus brokers de Kafka en esos entornos (ej., en Kubernetes, VMs, etc.) estén configurados para escuchar conexiones SASL_PLAINTEXT y tengan los usuarios SASL definidos (con el mecanismo SCRAM-SHA-512).

Por ejemplo, si desplegaras en Kubernetes, el StatefulSet de Kafka necesitaría las variables de entorno o la configuración para habilitar el listener SASL_PLAINTEXT y el JAAS configuration para el broker, de manera similar a como lo tenemos en tu docker-compose.yml para desarrollo.



kafka/config/kafka/broker_jaas.config -> Este archivo le dice al broker de Kafka cómo autenticar a los clientes.
kafka/config/kafka/client_jaas.config -> Este archivo es utilizado por las herramientas de línea de comandos de Kafka (como kafka-topics en el healthcheck) y por tus clientes (como kafka-topic-initializer y tu backend_api) para autenticarse con el broker.

## TODO: Para fase de MVP se dejar seteado a PLAINTEXT todos los ambientes, pero OJO, esto no es recomendable en ambiente real. Hay que colocarle los certificados. 