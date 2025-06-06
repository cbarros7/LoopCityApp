# --- Etapa de Construcción (Build Stage) ---
# Usamos una imagen base oficial de Python. Es buena práctica usar versiones específicas.
FROM python:3.11-slim-buster AS builder

# Establece variables de entorno para Poetry
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV POETRY_NO_INTERACTION=1
ENV POETRY_CACHE_DIR="/tmp/poetry_cache"

# Añade Poetry al PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Instala Poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Copia los archivos de configuración del proyecto Poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Instala las dependencias del proyecto usando Poetry
# --no-root: No instala el paquete del proyecto en sí (ya que es un script standalone)
# --no-dev: No instala las dependencias de desarrollo (como pytest)
RUN poetry install --no-root --no-dev

# --- Etapa Final (Final Stage) ---
# Usa una imagen más limpia y pequeña para el runtime final
FROM python:3.11-slim-buster

# Establece el directorio de trabajo
WORKDIR /app

# Copia el entorno virtual de Poetry de la etapa de construcción a la etapa final
COPY --from=builder /app/.venv /app/.venv

# Copia tu script principal
COPY main.py .
# Si tu código está en una subcarpeta (ej. 'src/'):
# COPY src/ ./src/

# Añade el binario del entorno virtual de Poetry al PATH
ENV PATH="/app/.venv/bin:$PATH"

# Comando para ejecutar tu script cuando el contenedor se inicie
# Usa 'poetry run' para asegurar que el script se ejecuta en el entorno virtual de Poetry
CMD ["python", "main.py"]
