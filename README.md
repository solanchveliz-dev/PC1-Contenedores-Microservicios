# PC1 - Contenedores y Microservicios

Práctica Calificada 1 del curso Desarrollo de Soluciones en la Nube.

## Datos generales

- **Estudiante:** Naomi Veliz
- **Curso:** Desarrollo de Soluciones en la Nube
- **Tema:** Contenedores, Dockerfiles y Docker Compose
- **Repositorio:** PC1-Contenedores-Microservicios

## Descripción

Este repositorio contiene dos aplicaciones web desarrolladas con Python y Flask. Cada caso incluye un Dockerfile base, un Dockerfile optimizado y un Dockerfile multistage. El Caso 1 incluye además un archivo `docker-compose.yml` para levantarlo con un solo comando.

- **Caso 1:** aplicación para descargar videos públicos o autorizados.
- **Caso 2:** aplicación para registrar resultados consultados en ONPE y generar un archivo Excel.

## Estructura del proyecto

```
PC1-Contenedores-Microservicios/
├── caso1-descargador-videos/
│   ├── app.py
│   ├── requirements.txt
│   ├── docker-compose.yml
│   ├── templates/
│   │   └── index.html
│   ├── descargas/
│   ├── Dockerfile
│   ├── Dockerfile.optimizado
│   ├── Dockerfile.multistage
│   └── .dockerignore
│
├── caso2-consulta-electoral/
│   ├── app.py
│   ├── requirements.txt
│   ├── templates/
│   │   └── index.html
│   ├── datos/
│   ├── Dockerfile
│   ├── Dockerfile.optimizado
│   ├── Dockerfile.multistage
│   └── .dockerignore
│
├── .gitignore
└── README.md
```

## Requisitos

Antes de ejecutar el proyecto se necesita:

- Docker Desktop
- Git
- Navegador web
- Docker Desktop iniciado

Verificar Docker:

```
docker version
docker compose version
```

Clonar el repositorio:

```
git clone https://github.com/solanchveliz-dev/PC1-Contenedores-Microservicios.git
cd PC1-Contenedores-Microservicios
```

---

## Caso 1: Descargador de videos

### Descripción

Aplicación web que permite descargar videos de las siguientes plataformas:

- YouTube
- Instagram
- TikTok
- Facebook
- LinkedIn
- Otras redes compatibles con yt-dlp (X, Threads, Reddit, Vimeo, entre otras)

La aplicación identifica la plataforma mediante el dominio del enlace y utiliza yt-dlp para procesar contenido público o autorizado. Todos los videos se entregan en formato MP4 compatible con cualquier reproductor, con imagen y sonido.

### Uso responsable

La aplicación debe utilizarse únicamente para contenido propio, de dominio público o para el cual se tenga autorización. Algunos enlaces pueden requerir autenticación o presentar restricciones establecidas por la plataforma.

### Ejecución rápida con Docker Compose (recomendado)

Desde la raíz del repositorio:

```
cd caso1-descargador-videos
docker compose up --build
```

Esperar hasta que aparezca `Running on http://0.0.0.0:5000` y abrir en el navegador:

http://localhost:8000

Pegar el enlace de un video, marcar la casilla de autorización y presionar descargar.

Verificar el estado (en otra terminal, dentro de `caso1-descargador-videos`):

```
docker compose ps
```

Debe mostrar `Up` y `(healthy)`.

Detener la aplicación: `Ctrl + C` y luego:

```
docker compose down
```

> Se usa el puerto **8000** porque en macOS el puerto 5000 está ocupado por AirPlay.

### Construir la imagen base

```
cd caso1-descargador-videos
docker build -t descargador-videos:v1.0 .
```

### Ejecutar el contenedor

```
docker run -d -p 8000:5000 --name descargador-videos-container descargador-videos:v1.0
```

Abrir en el navegador:

http://localhost:8000

### Construir la imagen optimizada

```
docker build -f Dockerfile.optimizado -t descargador-videos:v1.1-alpine .
```

### Construir la imagen multistage

```
docker build -f Dockerfile.multistage -t descargador-videos:v1.2-multistage .
```

### Comparar las imágenes

```
docker images descargador-videos
```

---

## Caso 2: Registro electoral

### Descripción

Aplicación web que permite registrar los resultados obtenidos después de consultar un DNI en el portal oficial de ONPE.

Portal oficial:

https://consultaelectoral.onpe.gob.pe/inicio

La aplicación registra:

- DNI
- Condición de miembro de mesa
- Nombres y apellidos
- Región
- Provincia
- Distrito
- Dirección del local de votación
- Fecha de registro

Los datos se almacenan en un archivo Excel generado con openpyxl.

### Procedimiento de consulta

1. Ingresar al portal oficial de ONPE.
2. Realizar la consulta del DNI.
3. Registrar manualmente el resultado en la aplicación.
4. Indicar si la persona es miembro de mesa.
5. Si es miembro, registrar nombres, ubicación y dirección.
6. Descargar el archivo Excel generado.

La aplicación no automatiza el portal oficial ni intenta evitar sus verificaciones de seguridad.

### Construir la imagen base

Desde la raíz del repositorio:

```
cd caso2-consulta-electoral
docker build -t consulta-electoral:v1.0 .
```

### Ejecutar el contenedor

El Caso 2 utiliza el puerto 5001 para poder ejecutarse junto con el Caso 1:

```
docker run -d -p 5001:5000 --name consulta-electoral-container consulta-electoral:v1.0
```

Abrir en el navegador:

http://localhost:5001

### Construir la imagen optimizada

```
docker build -f Dockerfile.optimizado -t consulta-electoral:v1.1-alpine .
```

### Construir la imagen multistage

```
docker build -f Dockerfile.multistage -t consulta-electoral:v1.2-multistage .
```

### Comparar las imágenes

```
docker images consulta-electoral
```

---

## Verificación de los contenedores

### Listar contenedores activos

```
docker ps
```

### Consultar los logs

```
docker logs descargador-videos-container
docker logs consulta-electoral-container
```

Si el Caso 1 se levantó con Docker Compose, desde `caso1-descargador-videos`:

```
docker compose logs
```

### Verificar el estado de salud del Caso 2

```
docker inspect --format="{{.State.Health.Status}}" consulta-electoral-container
```

### Detener los contenedores

```
docker stop descargador-videos-container
docker stop consulta-electoral-container
```

### Volver a iniciar los contenedores

```
docker start descargador-videos-container
docker start consulta-electoral-container
```

### Eliminar los contenedores

Primero deben estar detenidos:

```
docker rm descargador-videos-container
docker rm consulta-electoral-container
```

---

## Versiones generadas

| Caso | Imagen base | Imagen optimizada | Imagen multistage |
|---|---|---|---|
| Caso 1 | descargador-videos:v1.0 | descargador-videos:v1.1-alpine | descargador-videos:v1.2-multistage |
| Caso 2 | consulta-electoral:v1.0 | consulta-electoral:v1.1-alpine | consulta-electoral:v1.2-multistage |

## Tecnologías utilizadas

- Python 3.11
- Flask
- Docker
- Docker Desktop
- Docker Compose
- HTML y CSS
- yt-dlp
- curl_cffi
- FFmpeg
- Deno
- openpyxl

## Protección de información

Los archivos Excel, videos descargados, entornos virtuales y datos generados durante la ejecución no se incluyen en el repositorio.

Para las demostraciones se utilizan datos ficticios. No se deben publicar DNI ni resultados electorales reales.

## Conclusiones

- Docker permite empaquetar la aplicación con todas sus dependencias.
- Docker Compose permite levantar la aplicación con un solo comando, sin escribir `docker build` y `docker run` por separado.
- Las imágenes permiten ejecutar el proyecto de manera consistente en diferentes computadoras.
- El orden de las instrucciones del Dockerfile ayuda a aprovechar la caché.
- Las imágenes Alpine pueden reducir el tamaño de la imagen final.
- Los builds multistage separan la instalación de dependencias de la etapa de ejecución.
- Ejecutar el contenedor con un usuario sin privilegios mejora su seguridad.
- Los health checks permiten comprobar si una aplicación responde correctamente.
- El Caso 2 genera automáticamente el archivo Excel solicitado.
