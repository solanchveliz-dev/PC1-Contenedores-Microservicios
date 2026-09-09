# PC1 - Contenedores y Microservicios

Práctica Calificada 1 del curso Desarrollo de Soluciones en la Nube.

## Datos generales

- **Estudiante:** Naomi Veliz
- **Curso:** Desarrollo de Soluciones en la Nube
- **Tema:** Contenedores y Dockerfiles
- **Repositorio:** [PC1-Contenedores-Microservicios](https://github.com/solanchveliz-dev/PC1-Contenedores-Microservicios)

## Descripción

Este repositorio contiene dos aplicaciones web desarrolladas con Python y Flask. Cada caso incluye un Dockerfile base, un Dockerfile optimizado y un Dockerfile multistage.

- **Caso 1:** aplicación para descargar videos públicos o autorizados.
- **Caso 2:** aplicación para registrar resultados consultados en ONPE y generar un archivo Excel.

## Estructura del proyecto

```text
PC1-Contenedores-Microservicios/
├── caso1-descargador-videos/
│   ├── app.py
│   ├── requirements.txt
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

```bash
docker version
```

---

# Caso 1: Descargador de videos

## Descripción

Aplicación web que permite descargar videos de las siguientes plataformas:

- YouTube
- Instagram
- TikTok
- Facebook
- LinkedIn

La aplicación identifica la plataforma mediante el dominio del enlace y utiliza `yt-dlp` para procesar contenido público o autorizado.

## Uso responsable

La aplicación debe utilizarse únicamente para contenido propio, de dominio público o para el cual se tenga autorización. Algunos enlaces pueden requerir autenticación o presentar restricciones establecidas por la plataforma.

## Construir la imagen base

```bash
cd caso1-descargador-videos
docker build -t descargador-videos:v1.0 .
```

## Ejecutar el contenedor

```bash
docker run -d -p 5000:5000 --name descargador-videos-container descargador-videos:v1.0
```

Abrir en el navegador:

[http://localhost:5000](http://localhost:5000)

## Construir la imagen optimizada

```bash
docker build -f Dockerfile.optimizado -t descargador-videos:v1.1-alpine .
```

## Construir la imagen multistage

```bash
docker build -f Dockerfile.multistage -t descargador-videos:v1.2-multistage .
```

## Comparar las imágenes

```bash
docker images | findstr descargador-videos
```

---

# Caso 2: Registro electoral

## Descripción

Aplicación web que permite registrar los resultados obtenidos después de consultar un DNI en el portal oficial de ONPE.

Portal oficial:

[https://consultaelectoral.onpe.gob.pe/inicio](https://consultaelectoral.onpe.gob.pe/inicio)

La aplicación registra:

- DNI
- Condición de miembro de mesa
- Nombres y apellidos
- Región
- Provincia
- Distrito
- Dirección del local de votación
- Fecha de registro

Los datos se almacenan en un archivo Excel generado con `openpyxl`.

## Procedimiento de consulta

1. Ingresar al portal oficial de ONPE.
2. Realizar la consulta del DNI.
3. Registrar manualmente el resultado en la aplicación.
4. Indicar si la persona es miembro de mesa.
5. Si es miembro, registrar nombres, ubicación y dirección.
6. Descargar el archivo Excel generado.

La aplicación no automatiza el portal oficial ni intenta evitar sus verificaciones de seguridad.

## Construir la imagen base

Desde la raíz del repositorio:

```bash
cd caso2-consulta-electoral
docker build -t consulta-electoral:v1.0 .
```

## Ejecutar el contenedor

El Caso 2 utiliza el puerto `5001` para poder ejecutarse junto con el Caso 1:

```bash
docker run -d -p 5001:5000 --name consulta-electoral-container consulta-electoral:v1.0
```

Abrir en el navegador:

[http://localhost:5001](http://localhost:5001)

## Construir la imagen optimizada

```bash
docker build -f Dockerfile.optimizado -t consulta-electoral:v1.1-alpine .
```

## Construir la imagen multistage

```bash
docker build -f Dockerfile.multistage -t consulta-electoral:v1.2-multistage .
```

## Comparar las imágenes

En Windows PowerShell:

```powershell
docker images | findstr consulta-electoral
```

---

# Verificación de los contenedores

## Listar contenedores activos

```bash
docker ps
```

## Consultar los logs

```bash
docker logs descargador-videos-container
docker logs consulta-electoral-container
```

## Verificar el estado de salud del Caso 2

En Windows PowerShell:

```powershell
docker inspect --format="{{.State.Health.Status}}" consulta-electoral-container
```

## Detener los contenedores

```bash
docker stop descargador-videos-container
docker stop consulta-electoral-container
```

## Volver a iniciar los contenedores

```bash
docker start descargador-videos-container
docker start consulta-electoral-container
```

## Eliminar los contenedores

Primero deben estar detenidos:

```bash
docker rm descargador-videos-container
docker rm consulta-electoral-container
```

# Versiones generadas

| Caso | Imagen base | Imagen optimizada | Imagen multistage |
|---|---|---|---|
| Caso 1 | `descargador-videos:v1.0` | `descargador-videos:v1.1-alpine` | `descargador-videos:v1.2-multistage` |
| Caso 2 | `consulta-electoral:v1.0` | `consulta-electoral:v1.1-alpine` | `consulta-electoral:v1.2-multistage` |

# Tecnologías utilizadas

- Python 3.11
- Flask
- Docker
- Docker Desktop
- HTML y CSS
- yt-dlp
- FFmpeg
- Deno
- openpyxl

# Protección de información

Los archivos Excel, videos descargados, entornos virtuales y datos generados durante la ejecución no se incluyen en el repositorio.

Para las demostraciones se utilizan datos ficticios. No se deben publicar DNI ni resultados electorales reales.

# Conclusiones

- Docker permite empaquetar la aplicación con todas sus dependencias.
- Las imágenes permiten ejecutar el proyecto de manera consistente en diferentes computadoras.
- El orden de las instrucciones del Dockerfile ayuda a aprovechar la caché.
- Las imágenes Alpine pueden reducir el tamaño de la imagen final.
- Los builds multistage separan la instalación de dependencias de la etapa de ejecución.
- Ejecutar el contenedor con un usuario sin privilegios mejora su seguridad.
- Los health checks permiten comprobar si una aplicación responde correctamente.
- El Caso 2 genera automáticamente el archivo Excel solicitado.