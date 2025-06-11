#!/bin/bash
set -ex # Mantén 'x' para el debugging. Quítalo una vez que funcione.

echo "Esperando que MongoDB inicie..."
# ... (código existente para esperar a MongoDB) ...

echo "Inicializando el replica set y creando usuario de aplicación..."

# ... (código existente para rs.initiate) ...

# ... (código existente para esperar al primario) ...

# AÑADE ESTE BLOQUE: Bucle de reintento para la creación de usuario
USER_CREATION_RETRIES=10 # Número de intentos máximos
RETRY_COUNT=0
USER_CREATED=false

echo "Primario del replica set detectado y estabilizado. Intentando crear usuario de aplicación..."

while [ "$RETRY_COUNT" -lt "$USER_CREATION_RETRIES" ] && [ "$USER_CREATED" = false ]; do
  echo "Intento $((RETRY_COUNT + 1)) de crear usuario de aplicación..."
  # Ejecuta el script para crear el usuario de la aplicación.
  # El 'if ...; then ... else ... fi' captura el código de salida del comando.
  if mongosh --host mongodb1 -u "${MONGO_ROOT_USERNAME}" -p "${MONGO_ROOT_PASSWORD}" --authenticationDatabase admin \
    --eval "var appUsername='${MONGO_APP_USERNAME}'; var appPassword='${MONGO_APP_PASSWORD}'; var appDatabase='${MONGO_APP_DATABASE}';" \
    /scripts/create_app_user.js; then
    USER_CREATED=true
    echo "Usuario de aplicación creado exitosamente en el intento $((RETRY_COUNT + 1))."
  else
    echo "Fallo en el intento $((RETRY_COUNT + 1)). El primario podría haber cambiado o hay un problema transitorio. Reintentando en 5 segundos..."
    sleep 30
    RETRY_COUNT=$((RETRY_COUNT + 1))
  fi
done

if [ "$USER_CREATED" = false ]; then
  echo "Error: No se pudo crear el usuario de aplicación después de múltiples reintentos. Revise la estabilidad del replica set y los logs de los nodos MongoDB."
  exit 1
fi
# --- FIN DEL BLOQUE DE REINTENTO ---

echo "Configuración de MongoDB completada."