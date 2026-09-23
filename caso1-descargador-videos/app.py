from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as TiempoAgotado
import json
import os
import socket
import subprocess

from flask import Flask, render_template, request, send_from_directory
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "descargas"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Tiempo maximo que la pagina espera una descarga (en segundos).
# Asi la pagina NUNCA se queda cargando para siempre.
TIEMPO_MAXIMO = int(os.environ.get("TIEMPO_MAXIMO", 180))
trabajos = ThreadPoolExecutor(max_workers=4)


# Solo sirve para mostrar un nombre bonito.
# Si el enlace no esta aqui, igual se intenta descargar.
PLATAFORMAS = {
    "YouTube": ("youtube.com", "youtu.be", "youtube-nocookie.com"),
    "Instagram": ("instagram.com",),
    "TikTok": ("tiktok.com",),
    "Facebook": ("facebook.com", "fb.watch", "fb.com"),
    "LinkedIn": ("linkedin.com",),
    "X (Twitter)": ("x.com", "twitter.com"),
    "Threads": ("threads.net", "threads.com"),
    "Reddit": ("reddit.com", "redd.it"),
    "Pinterest": ("pinterest.com", "pin.it"),
    "Vimeo": ("vimeo.com",),
    "Twitch": ("twitch.tv",),
    "Dailymotion": ("dailymotion.com", "dai.ly"),
    "Kick": ("kick.com",),
}

# Orden en que se elige el formato:
# 1) video H.264 + audio m4a, unidos en MP4
# 2) video mp4 + audio m4a
# 3) archivo MP4 que ya trae video y audio (TikTok, LinkedIn...)
# 4) lo mejor que haya
FORMATO_PRINCIPAL = "bv*[vcodec^=avc1]+ba[ext=m4a]/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"

# Si el video salio sin sonido: pedir un archivo con audio incluido
FORMATO_CON_AUDIO = "b[acodec!=none]/b"


def es_url_valida(url):
    """Comprueba que el texto sea un enlace http o https."""
    partes = urlparse(url)
    return partes.scheme in ("http", "https") and bool(partes.hostname)


def detectar_plataforma(url):
    """Identifica la red social utilizando el dominio del enlace."""
    dominio = (urlparse(url).hostname or "").lower()
    dominio = dominio.removeprefix("www.")

    for plataforma, dominios in PLATAFORMAS.items():
        if any(
            dominio == permitido or dominio.endswith("." + permitido)
            for permitido in dominios
        ):
            return plataforma

    return None


def crear_opciones(formato, preferir_h264=True):
    """Configuracion de yt-dlp."""
    return {
        "format": formato,
        # IMPORTANTE: no se fuerza H.264 al elegir, porque en TikTok eso manda
        # a un servidor que a veces no responde. La compatibilidad con
        # QuickTime se arregla DESPUES en hacer_compatible().
        "merge_output_format": "mp4",
        "outtmpl": str(DOWNLOAD_DIR / "%(title).80s-%(id)s.%(ext)s"),
        "noplaylist": True,
        "overwrites": True,
        "restrictfilenames": True,
        # Muestra en la Terminal de Docker cada paso (sirve para revisar)
        "quiet": False,
        "noprogress": True,
        "no_warnings": False,
        "no_color": True,
        # Si el servidor no responde, rendirse rapido y probar otra opcion
        "retries": 1,
        "fragment_retries": 1,
        "extractor_retries": 2,
        "socket_timeout": 15,
        # Forzar IPv4: Docker en Mac a veces intenta conectarse por IPv6
        # y la conexion se queda colgada (timeout)
        "source_address": "0.0.0.0",
        # Necesario para YouTube
        "js_runtimes": {"deno": {}},
        "remote_components": {"ejs:github"},
    }


def buscar_archivo(informacion):
    """Devuelve la ruta del video ya descargado."""
    descargas = informacion.get("requested_downloads") or []
    if descargas and descargas[0].get("filepath"):
        ruta = Path(descargas[0]["filepath"])
        if ruta.exists():
            return ruta

    candidatos = sorted(
        DOWNLOAD_DIR.glob(f"*{informacion.get('id', '')}*"),
        key=lambda r: r.stat().st_mtime,
        reverse=True,
    )
    return candidatos[0] if candidatos else None


def revisar_codecs(ruta):
    """Devuelve (codec de video, codec de audio). None si no tiene esa pista."""
    try:
        resultado = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=codec_type,codec_name",
                "-of", "json",
                str(ruta),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        pistas = json.loads(resultado.stdout or "{}").get("streams", [])
    except Exception:
        # Si no se puede revisar, asumimos que esta bien
        return "h264", "aac"

    video = next((p["codec_name"] for p in pistas if p.get("codec_type") == "video"), None)
    audio = next((p["codec_name"] for p in pistas if p.get("codec_type") == "audio"), None)
    return video, audio


def hacer_compatible(ruta):
    """
    Convierte el video a MP4 con H.264 + AAC si hace falta,
    para que se vea y se escuche en cualquier reproductor (QuickTime, celular, etc.).
    """
    video, audio = revisar_codecs(ruta)

    if video == "h264" and audio in ("aac", None) and ruta.suffix == ".mp4":
        return ruta  # ya es compatible

    salida = ruta.with_name(ruta.stem + "-compatible.mp4")

    comando = ["ffmpeg", "-y", "-v", "error", "-i", str(ruta)]

    if video == "h264":
        # Ya es compatible: se copia tal cual (instantaneo)
        comando += ["-c:v", "copy"]
    elif video == "hevc":
        # HEVC (TikTok): QuickTime lo reproduce si se marca como "hvc1".
        # Solo se cambia la etiqueta, NO se convierte (instantaneo)
        comando += ["-c:v", "copy", "-tag:v", "hvc1"]
    else:
        # VP9 / AV1 (Instagram, algunos de YouTube): hay que convertir.
        # "ultrafast" = conversion rapida
        comando += [
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-pix_fmt", "yuv420p",
        ]
    if audio is not None:
        comando += ["-c:a", "copy"] if audio == "aac" else ["-c:a", "aac", "-b:a", "160k"]
    comando += ["-movflags", "+faststart", str(salida)]

    try:
        subprocess.run(comando, check=True, capture_output=True, timeout=900)
    except Exception:
        # Si la conversion falla, se entrega el archivo original
        salida.unlink(missing_ok=True)
        return ruta

    ruta.unlink(missing_ok=True)
    final = ruta.with_suffix(".mp4")
    salida.rename(final)
    return final


def descargar(url, formato, preferir_h264=True):
    """Descarga el video y devuelve (informacion, ruta del archivo)."""
    with YoutubeDL(crear_opciones(formato, preferir_h264)) as descargador:
        informacion = descargador.extract_info(url, download=True)
    return informacion, buscar_archivo(informacion)


def descargar_con_respaldo(url):
    """
    1er intento: formato H.264 (el mas compatible).
    Si falla (por ejemplo, un servidor de TikTok no responde),
    se prueban las otras versiones del video una por una.
    Cada version suele estar guardada en un servidor distinto.
    """
    try:
        return descargar(url, FORMATO_PRINCIPAL)
    except DownloadError as primer_error:
        ultimo_error = primer_error

    # Pedir la lista de versiones disponibles (sin descargar)
    with YoutubeDL(crear_opciones("b", preferir_h264=False)) as descargador:
        informacion = descargador.extract_info(url, download=False)

    formatos = [
        f for f in informacion.get("formats") or []
        if f.get("vcodec") != "none" and f.get("format_id")
    ]
    # yt-dlp las ordena de peor a mejor: se invierte.
    # Primero las que ya traen audio y luego las H.264.
    formatos.reverse()
    formatos.sort(key=lambda f: (
        f.get("acodec") == "none",
        not str(f.get("vcodec", "")).startswith(("h264", "avc1")),
    ))

    for formato in formatos[:5]:
        try:
            return descargar(url, formato["format_id"], preferir_h264=False)
        except DownloadError as error:
            ultimo_error = error

    raise ultimo_error


def procesar(url):
    """Descarga, revisa el audio y deja el video compatible."""
    informacion, ruta = descargar_con_respaldo(url)

    # Si salio sin sonido, se borra y se intenta con otro formato
    if ruta is not None and revisar_codecs(ruta)[1] is None:
        ruta.unlink(missing_ok=True)
        informacion, ruta = descargar(url, FORMATO_CON_AUDIO, preferir_h264=False)

    if ruta is not None:
        ruta = hacer_compatible(ruta)

    return informacion, ruta


@app.route("/", methods=["GET", "POST"])
def inicio():
    mensaje = None
    error = None
    archivo = None
    plataforma = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        autorizado = request.form.get("autorizado")

        if not url:
            error = "Debes ingresar el enlace de un video."
        elif not es_url_valida(url):
            error = "El enlace debe empezar con http:// o https://"
        elif autorizado != "si":
            error = "Debes confirmar que tienes permiso para descargar el contenido."
        else:
            plataforma = detectar_plataforma(url)

            try:
                trabajo = trabajos.submit(procesar, url)
                informacion, ruta = trabajo.result(timeout=TIEMPO_MAXIMO)

                # Si el enlace era de una web que no esta en la lista,
                # usamos el nombre que detecta yt-dlp
                if plataforma is None:
                    plataforma = informacion.get("extractor_key", "otra plataforma")

                if ruta is None:
                    error = "El video se proceso pero no se encontro el archivo."
                else:
                    archivo = ruta.name
                    mensaje = f"Video de {plataforma} descargado correctamente."
                    if revisar_codecs(ruta)[1] is None:
                        mensaje += " (El video original no tiene sonido.)"

            except TiempoAgotado:
                error = (
                    f"La red social tardo mas de {TIEMPO_MAXIMO} segundos en responder. "
                    "Intenta de nuevo en un momento o prueba con otro enlace."
                )
            except DownloadError as excepcion:
                detalle = str(excepcion).replace("ERROR: ", "")
                error = (
                    "No se pudo descargar el video. Puede ser privado, "
                    f"requerir iniciar sesion o no ser compatible. Detalle: {detalle}"
                )
            except Exception as excepcion:
                error = f"Ocurrio un error inesperado: {excepcion}"

    return render_template(
        "index.html",
        mensaje=mensaje,
        error=error,
        archivo=archivo,
        plataforma=plataforma,
        hostname=socket.gethostname(),
    )


@app.route("/descargas/<path:nombre_archivo>")
def descargar_archivo(nombre_archivo):
    """Entrega al navegador un video que ya fue descargado."""
    return send_from_directory(DOWNLOAD_DIR, nombre_archivo, as_attachment=True)


@app.route("/health")
def health():
    """Permite a Docker comprobar que la aplicacion esta funcionando."""
    return {"estado": "saludable"}, 200


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)