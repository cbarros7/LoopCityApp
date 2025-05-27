#!/bin/bash
# entrypoint.sh

# Script de entrada para el contenedor kafka-topic-initializer.

echo "Iniciando el script de inicialización de topics con Poetry..."

# Ejecutar el script de Python utilizando Poetry
# Pasa cualquier argumento de línea de comandos (ej. el ambiente)
# directamente al script Python.
poetry run python /app/src/kafka_manager.py "$@"

# Si el script python termina con un error, el contenedor también lo hará.
# Si termina exitosamente, el contenedor se cerrará.
echo "Script de inicialización de topics finalizado."