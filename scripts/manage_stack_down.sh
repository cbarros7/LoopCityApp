#!/bin/bash

# --- Configuración ---
# Navega al directorio raíz de tu proyecto donde se encuentra docker-compose.yaml
cd "$(dirname "$0")/.."

export COMPOSE_PROJECT_NAME="LOOPCITYAPP"

# --- Lógica Principal ---
echo "--- Gestión de Bajada de Stack Docker Compose ---"

# Verifica si se proporcionaron argumentos
if [ -z "$1" ]; then
    echo "Modo de uso: ./scripts/manage_stack_down.sh <opcion> [servicio1] [servicio2]..."
    echo "Opciones:"
    echo "  full            : Baja (detiene y elimina) todo el stack, preservando los datos de los volúmenes nombrados."
    echo "  <servicio_nombre> : Detiene un servicio específico (sin eliminarlo, para reiniciar luego)."
    echo "  <servicio1> <servicio2> : Detiene varios servicios."
    echo ""
    echo "Ejemplos:"
    echo "  ./scripts/manage_stack_down.sh full"
    echo "  ./scripts/manage_stack_down.sh kafka"
    echo "  ./scripts/manage_stack_down.sh backend_api mongodb1"
    echo ""
    echo "Para eliminar los datos de los volúmenes, usa 'docker-compose -p ${COMPOSE_PROJECT_NAME} down -v'."
    exit 1
fi

ACTION=$1
shift # Elimina el primer argumento (la acción) para que $1, $2, etc., sean los nombres de los servicios

case "$ACTION" in
    full)
        echo "Bajando el stack COMPLETO (los datos de los volúmenes persistirán)..."
        # --remove-orphans: elimina contenedores de servicios que ya no están definidos.
        # NOTA: 'docker-compose down' por defecto NO elimina los volúmenes nombrados.
        docker-compose -p "${COMPOSE_PROJECT_NAME}" down --remove-orphans
        ;;
    *) # Si la acción no es 'full', asumimos que los argumentos son nombres de servicios
        # Restauramos el primer argumento si era un nombre de servicio
        set -- "$ACTION" "$@"
        SERVICES="$@"
        echo "Deteniendo servicios específicos: ${SERVICES}..."
        # 'docker-compose stop' detiene los contenedores pero no los elimina.
        docker-compose -p "${COMPOSE_PROJECT_NAME}" stop ${SERVICES}
        ;;
esac

if [ $? -eq 0 ]; then
    echo "Operación de bajada finalizada exitosamente."
    echo "Para ver el estado de los servicios: docker-compose -p ${COMPOSE_PROJECT_NAME} ps"
else
    echo "Hubo un error durante la operación de bajada."
    exit 1
fi