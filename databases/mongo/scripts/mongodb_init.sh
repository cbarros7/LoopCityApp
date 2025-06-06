#!/bin/bash
# ./databases/mongo/scripts/mongodb_init.sh

# Espera a que el primer nodo de MongoDB esté listo para aceptar conexiones
echo "Esperando que MongoDB (mongodb1) esté listo..."
until mongosh --host mongodb1 -u ${MONGO_ROOT_USERNAME} -p ${MONGO_ROOT_PASSWORD} --authenticationDatabase admin --eval 'quit()' > /dev/null 2>&1; do
  printf '.'
  sleep 1
done
echo "MongoDB (mongodb1) está listo."

# Inicia el replica set (esto solo se ejecuta la primera vez)
echo "Iniciando el replica set rs0..."
mongosh --host mongodb1 --eval "var config = { _id: \"${MONGO_REPLICA_SET_NAME}\", members: [{ _id: 0, host: \"mongodb1:27017\" }, { _id: 1, host: \"mongodb2:27017\" }, { _id: 2, host: \"mongodb3:27017\" }] }; rs.initiate(config, { force: true });"

# Espera a que el replica set esté configurado y primario elegido
echo "Esperando que el replica set esté configurado y primario elegido..."
until mongosh --host mongodb1 --eval 'rs.status().ok' > /dev/null 2>&1; do
  printf '.'
  sleep 1
done

# Espera a que el primario del replica set esté listo para aceptar conexiones
# y para que el usuario root se replique
echo "Esperando que el primario esté listo con autenticación..."
until mongosh --host mongodb1 -u ${MONGO_ROOT_USERNAME} -p ${MONGO_ROOT_PASSWORD} --authenticationDatabase admin --eval 'db.runCommand({ ping: 1 }).ok' > /dev/null 2>&1; do
  printf '.'
  sleep 1
done

echo "Primario del replica set rs0 listo con autenticación."

# Crear usuario de aplicación
echo "Creando usuario de aplicación en MongoDB..."
mongosh --host mongodb1 -u ${MONGO_ROOT_USERNAME} -p ${MONGO_ROOT_PASSWORD} --authenticationDatabase admin /scripts/create_app_user.js

echo "Usuario de aplicación creado."

echo "Proceso de inicialización de MongoDB completado."