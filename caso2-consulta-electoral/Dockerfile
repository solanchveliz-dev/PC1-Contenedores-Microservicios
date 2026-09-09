# Imagen oficial de Python
FROM python:3.11-slim

# Información de la imagen
LABEL maintainer="solanch.veliz@tecsup.edu.pe"
LABEL description="Registro electoral y generación de Excel"

# Evita archivos innecesarios y muestra los logs inmediatamente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia la aplicación y la interfaz
COPY app.py .
COPY templates ./templates

# Crea la carpeta para guardar el Excel
RUN mkdir -p /app/datos

# Puerto utilizado por Flask
EXPOSE 5000

# Verifica que la aplicación esté funcionando
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Inicia la aplicación
CMD ["python", "app.py"]