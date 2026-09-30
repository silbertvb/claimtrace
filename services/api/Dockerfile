# Imagen base de Python ligera.
FROM python:3.12-slim

# Carpeta de trabajo dentro del contenedor.
WORKDIR /app

# Se copian y se instalan primero las dependencias: si solo cambia el código,
# Docker reutiliza esta capa y las builds son más rápidas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Usuario sin privilegios: si alguien explotara un fallo de la API, no tendría
# permisos de root dentro del contenedor.
RUN useradd --create-home --uid 1000 appuser

# Se copia el código con ese usuario como propietario.
COPY --chown=appuser:appuser . .

# A partir de aquí, todo se ejecuta como appuser.
USER appuser

# Arranca el servidor. 0.0.0.0 es necesario DENTRO del contenedor; desde fuera
# solo se llega por el puerto que publica el compose (127.0.0.1).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]