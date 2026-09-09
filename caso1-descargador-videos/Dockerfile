# Imagen base oficial de Python
FROM python:3.11-slim

# Información de la autora y del proyecto
LABEL maintainer="solanch.veliz@tecsup.edu.pe"
LABEL description="Aplicación web para descargar videos autorizados"

# Copiar Deno desde su imagen oficial
COPY --from=denoland/deno:bin-2.9.5 /deno /usr/local/bin/deno

# Evitar preguntas durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Instalar certificados y FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar e instalar las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --pre -r requirements.txt

# Copiar la aplicación y la interfaz
COPY app.py .
COPY templates ./templates

# Crear la carpeta de descargas
RUN mkdir -p /app/descargas

# Puerto utilizado por Flask
EXPOSE 5000

# Comando que inicia la aplicación
CMD ["python", "app.py"]