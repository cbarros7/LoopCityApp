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

# --- Configuración ---
# Navega al directorio raíz de tu proyecto donde se encuentra docker-compose.yaml
cd "$(dirname "$0")/.."

# Define el nombre de tu proyecto explícitamente (opcional, Docker lo infiere del directorio)
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME}"

# --- Función para verificar el demonio de Docker ---
check_docker_daemon() {
    echo "Verificando si el demonio de Docker está corriendo..."
    
    # Intenta un comando de Docker y redirige la salida para que no se muestre
    docker info > /dev/null 2>&1
    
    if [ $? -ne 0 ]; then
        # Docker NO está corriendo o no es accesible
        echo "========================================================"
        echo "  ¡ADVERTENCIA: Docker Desktop NO está corriendo!"
        echo "  Es necesario abrir la aplicación 'Docker Desktop'."
        echo "  Intentando abrir Docker Desktop ahora..."
        echo "========================================================"
        
        # Intenta abrir la aplicación Docker Desktop
        open -a Docker || { 
            echo "Error: No se pudo abrir la aplicación 'Docker Desktop'."
            echo "Por favor, iníciala manualmente desde tu Launchpad o la carpeta Aplicaciones."
            exit 1 
        }
        
        echo "Esperando a que Docker Desktop esté completamente operativo (esto puede tardar varios segundos)..."
        local max_attempts=60 # Aumentado a 60 intentos (2 minutos)
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            docker info > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo "" # Nueva línea después de los puntos de espera
                echo "Demonio de Docker operativo."
                return 0
            fi
            echo -n "." # Muestra un punto cada 2 segundos
            sleep 2
            attempt=$((attempt+1))
        done
        echo "" # Nueva línea final
        echo "Error: Docker Desktop no se levantó a tiempo. Por favor, revisa su estado manualmente."
        exit 1
    else
        # Docker ya está corriendo
        echo "El demonio de Docker ya está corriendo."
        return 0
    fi
}

# --- Lógica Principal ---
echo "--- Gestión de Subida de Stack Docker Compose ---"

# Llama a la función para verificar el demonio de Docker
check_docker_daemon

# --- Parseo de Argumentos ---
CLEAN_CACHE=false
SERVICES=""
ACTION=""

# Recorre los argumentos para encontrar flags y la acción
for arg in "$@"; do
    case "$arg" in
        --clean-cache|-c)
            CLEAN_CACHE=true
            ;;
        full)
            ACTION="full"
            ;;
        *)
            # Si no es un flag o 'full', asúmelo como un nombre de servicio
            if [ -z "$ACTION" ]; then # Solo si la acción principal no ha sido definida
                ACTION="partial" # Define la acción como parcial si se especifican servicios
            fi
            SERVICES+="$arg " # Acumula los nombres de los servicios
            ;;
    esac
done

# Si no se especificó ninguna acción (ej. solo se pasó --clean-cache)
if [ -z "$ACTION" ]; then
    echo "Modo de uso: ./scripts/manage_stack_up.sh <opcion> [--clean-cache|-c] [servicio1] [servicio2]..."
    echo "Opciones:"
    echo "  full            : Levanta todo el stack."
    echo "  <servicio_nombre> : Levanta un servicio específico y sus dependencias (ej. kafka)."
    echo "  <servicio1> <servicio2> : Levanta varios servicios y sus dependencias (ej. backend_api mongodb1)."
    echo "Flags opcionales:"
    echo "  --clean-cache, -c: Elimina el caché de construcción de las imágenes antes de levantarlas."
    echo ""
    echo "Ejemplos:"
    echo "  ./scripts/manage_stack_up.sh full"
    echo "  ./scripts/manage_stack_up.sh full --clean-cache"
    echo "  ./scripts/manage_stack_up.sh kafka"
    echo "  ./scripts/manage_stack_up.sh backend_api mongodb1 -c"
    exit 1
fi

# Elimina el espacio extra al final de SERVICES
SERVICES=$(echo "$SERVICES" | xargs)

# --- Ejecución de Comandos Basada en la Acción y el Flag ---
if [ "$CLEAN_CACHE" = true ]; then
    if [ "$ACTION" = "full" ]; then
        echo "Limpiando caché y reconstruyendo TODAS las imágenes..."
        docker-compose -p "${COMPOSE_PROJECT_NAME}" build --no-cache || { echo "Error al reconstruir imágenes."; exit 1; }
    else # Acción parcial con --clean-cache
        echo "Limpiando caché y reconstruyendo imágenes para servicios específicos: ${SERVICES}..."
        docker-compose -p "${COMPOSE_PROJECT_NAME}" build --no-cache ${SERVICES} || { echo "Error al reconstruir imágenes."; exit 1; }
    fi
fi

# Ahora, levantar los servicios
if [ "$ACTION" = "full" ]; then
    echo "Levantando el stack COMPLETO..."
    docker-compose -p "${COMPOSE_PROJECT_NAME}" up -d --build --remove-orphans 
else # Acción parcial
    echo "Levantando servicios específicos: ${SERVICES}"
    # --build se mantiene para que Docker Compose construya si no lo hizo antes o si hay cambios
    docker-compose -p "${COMPOSE_PROJECT_NAME}" up -d --build ${SERVICES}
fi

if [ $? -eq 0 ]; then
    echo "Operación de subida finalizada exitosamente."
    echo "Para ver el estado de los servicios: docker-compose -p ${COMPOSE_PROJECT_NAME} ps"
else
    echo "Hubo un error durante la operación de subida."
    exit 1
fi