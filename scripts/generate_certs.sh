#!/bin/bash

# --- Cargar variables de entorno desde .env ---
# Asumimos que .env está en el directorio padre de scripts/
echo "DEBUG: Checking for .env at: $(readlink -f ../.env)" # <-- Añade esta línea temporalmente para depurar
if [ -f ".env" ]; then
  set -a
  . ".env"
  set +a
  echo "DEBUG: .env file loaded for certificate generation."
else
  echo "WARNING: .env file not found at ../.env. Ensure it exists with SSL passwords defined."
  # Puedes salir aquí si las contraseñas son obligatorias, o usar valores por defecto.
  # Para un script de generación, es mejor que las passwords estén definidas.
  exit 1
fi
# --- Cargar variables de entorno ---

# Este script genera certificados auto-firmados para Kafka y sus clientes usando PKCS12.
# Está diseñado para entornos de desarrollo/prueba.

# Directorio de salida para los certificados
# Se crean en la raíz del proyecto, al mismo nivel que docker-compose.yaml
CERTS_DIR="ssl/" # <--- AJUSTE IMPORTANTE: Subir un nivel para crear 'ssl' en la raíz
mkdir -p "${CERTS_DIR}"

# Nombres comunes y contraseñas (ajusta según tus necesidades)
CA_CN="my-kafka-ca"
BROKER_CN="kafka" # Importante: Debe coincidir con el hostname de tu servicio Kafka
CLIENT_CN="kafka-client"

# Contraseñas para los Keystores y Truststores
# (Asegúrate de que estas sean seguras y las recuerdes o uses variables de entorno en producción)
KEYSTORE_PASSWORD="${SSL_KEYSTORE_PASSWORD}"
TRUSTSTORE_PASSWORD="${SSL_TRUSTSTORE_PASSWORD}"
KEY_PASSWORD="${SSL_KEY_PASSWORD}"

echo "Generando certificados en ${CERTS_DIR}..."

# 1. Generar la Clave Privada y Certificado para la CA
echo "Generando clave privada y certificado de la CA..."
openssl req -new -x509 -keyout "${CERTS_DIR}/ca.key" -out "${CERTS_DIR}/ca.crt" -days 3650 -passout pass:${KEYSTORE_PASSWORD} -subj "/CN=${CA_CN}/O=MyOrg/OU=MyUnit/L=MyCity/ST=MyState/C=US"

# 2. Generar la Clave Privada y Solicitud de Firma de Certificado (CSR) para el Broker
echo "Generando clave privada y CSR del broker..."
openssl req -new -nodes -keyout "${CERTS_DIR}/kafka.key" -out "${CERTS_DIR}/kafka.csr" -subj "/CN=${BROKER_CN}/O=MyOrg/OU=MyUnit/L=MyCity/ST=MyState/C=US"

# 3. Firmar el Certificado del Broker con la CA
echo "Firmando certificado del broker con la CA..."
openssl x509 -req -CA "${CERTS_DIR}/ca.crt" -CAkey "${CERTS_DIR}/ca.key" -in "${CERTS_DIR}/kafka.csr" -out "${CERTS_DIR}/kafka.crt" -days 3650 -CAcreateserial -passin pass:${KEYSTORE_PASSWORD} -extfile <(printf "subjectAltName=DNS:${BROKER_CN}")

# 4. Crear el Keystore del Broker (PKCS12)
echo "Creando keystore PKCS12 para el broker..."
openssl pkcs12 -export -in "${CERTS_DIR}/kafka.crt" -inkey "${CERTS_DIR}/kafka.key" -chain -CAfile "${CERTS_DIR}/ca.crt" -name "${BROKER_CN}" -out "${CERTS_DIR}/kafka.keystore.p12" -password pass:${KEYSTORE_PASSWORD}

# 5. Crear el Truststore del Broker (PKCS12)
echo "Creando truststore PKCS12 para el broker..."
keytool -import -trustcacerts -file "${CERTS_DIR}/ca.crt" -alias ${CA_CN} -keystore "${CERTS_DIR}/kafka.truststore.p12" -storepass ${TRUSTSTORE_PASSWORD} -noprompt -storetype PKCS12

# 6. Crear el Truststore del Cliente (PKCS12)
echo "Creando truststore PKCS12 para el cliente..."
keytool -import -trustcacerts -file "${CERTS_DIR}/ca.crt" -alias ${CA_CN} -keystore "${CERTS_DIR}/client.truststore.p12" -storepass ${TRUSTSTORE_PASSWORD} -noprompt -storetype PKCS12

echo "Limpiando archivos intermedios (opcional, para mantener el directorio limpio)..."
rm "${CERTS_DIR}/ca.key" "${CERTS_DIR}/kafka.key" "${CERTS_DIR}/kafka.csr" "${CERTS_DIR}/kafka.crt" "${CERTS_DIR}/ca.srl"

echo "¡Generación de certificados completada!"
echo "Archivos relevantes en ${CERTS_DIR}:"
ls "${CERTS_DIR}"