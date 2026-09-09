from pathlib import Path
from urllib.parse import urlparse
import os
import socket

from flask import Flask, render_template, request, send_from_directory
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "descargas"
DOWNLOAD_DIR.mkdir(exist_ok=True)


PLATAFORMAS = {
    "YouTube": ("youtube.com", "youtu.be"),
    "Instagram": ("instagram.com",),
    "TikTok": ("tiktok.com",),
    "Facebook": ("facebook.com", "fb.watch"),
    "LinkedIn": ("linkedin.com",),
}


def detectar_plataforma(url):
    """Identifica la red social utilizando el dominio del enlace."""
    dominio = (urlparse(url).hostname or "").lower()
    dominio = dominio.removeprefix("www.")

    for plataforma, dominios in PLATAFORMAS.items():
        if any(
            dominio == dominio_permitido
            or dominio.endswith("." + dominio_permitido)
            for dominio_permitido in dominios
        ):
            return plataforma

    return None


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
        elif autorizado != "si":
            error = "Debes confirmar que tienes permiso para descargar el contenido."
        else:
            plataforma = detectar_plataforma(url)

            if plataforma is None:
                error = (
                    "El enlace no pertenece a YouTube, Instagram, TikTok, "
                    "Facebook o LinkedIn."
                )
            else:
                opciones = {
              "format": "best[ext=mp4]/best",
             "outtmpl": str(
                 DOWNLOAD_DIR / "%(title).80s-%(id)s.%(ext)s"
    ),
    "noplaylist": True,
    "restrictfilenames": True,
    "quiet": True,
    "no_warnings": True,
    "js_runtimes": {
        "deno": {}
    },
    "remote_components": {
        "ejs:npm"
    },
}

                try:
                    with YoutubeDL(opciones) as descargador:
                        informacion = descargador.extract_info(
                            url,
                            download=True
                        )
                        ruta_generada = Path(
                            descargador.prepare_filename(informacion)
                        )

                    candidatos = sorted(
                        DOWNLOAD_DIR.glob(
                            f"*{informacion.get('id', '')}*"
                        ),
                        key=lambda ruta: ruta.stat().st_mtime,
                        reverse=True,
                    )

                    if candidatos:
                        ruta_generada = candidatos[0]

                    archivo = ruta_generada.name
                    mensaje = (
                        f"Video de {plataforma} descargado correctamente."
                    )

                except DownloadError:
                    error = (
                        "No se pudo descargar el video. Verifica que el enlace "
                        "sea público, válido y no requiera iniciar sesión."
                    )
                except Exception as excepcion:
                    error = f"Ocurrió un error inesperado: {excepcion}"

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
    return send_from_directory(
        DOWNLOAD_DIR,
        nombre_archivo,
        as_attachment=True,
    )


@app.route("/health")
def health():
    """Permite a Docker comprobar que la aplicación está funcionando."""
    return {"estado": "saludable"}, 200


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)