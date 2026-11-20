"""Actualización de la app desde GitHub Releases (repositorio CocinaArguinyano).

Flujo:
  1. check_latest()   consulta la última Release y compara su versión con la instalada.
  2. download()       descarga el APK comprobando su SHA-256 (el «digest» que publica GitHub).
  3. install_apk()    abre el instalador de Android (el usuario confirma con «Instalar»).

Android no permite instalar en silencio desde una app normal: siempre pide confirmación.
Además, sólo acepta la actualización si el APK está firmado con la misma clave que la
app instalada (ver docs/ANDROID.md, «Clave de firma»).
"""
import hashlib
import json
import os
import re
import urllib.request

import functions

APP_REPO = "alherca25/CocinaArguinyano"
RELEASES_API = f"https://api.github.com/repos/{APP_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{APP_REPO}/releases/latest"


def parse_version(text):
    """"v1.3.0" -> (1, 3, 0). Ignora prefijos y sufijos no numéricos."""
    nums = re.findall(r"\d+", str(text or "").split("-")[0])
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - len(nums[:3]))


def is_newer(latest, current):
    return parse_version(latest) > parse_version(current)


def check_latest(current_version, asset_prefix):
    """Devuelve la info de la versión nueva o None si la instalada es la última.

    info = {"version", "name", "url", "size", "sha256", "notes", "page"}
    "url" es None si la Release no tiene APK para esta app.
    """
    _, body = functions.http_request(RELEASES_API, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "CocinaRapida"})
    rel = json.loads(body.decode("utf-8"))
    tag = rel.get("tag_name", "")
    if not is_newer(tag, current_version):
        return None
    info = {"version": ".".join(map(str, parse_version(tag))), "name": "", "url": None,
            "size": 0, "sha256": "", "notes": (rel.get("body") or "").strip(),
            "page": rel.get("html_url") or RELEASES_PAGE}
    for asset in rel.get("assets", []):
        name = asset.get("name", "")
        if name.startswith(asset_prefix) and name.endswith(".apk"):
            digest = asset.get("digest") or ""
            info.update(name=name, url=asset.get("browser_download_url"),
                        size=int(asset.get("size") or 0),
                        sha256=digest.split(":", 1)[1] if digest.startswith("sha256:") else "")
            break
    return info


def download(url, dest, sha256="", progress=None, chunk_size=64 * 1024, timeout=60):
    """Descarga url en dest. progress(bytes_descargados, total). Lanza ValueError si el SHA-256 no coincide."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    digest = hashlib.sha256()
    req = urllib.request.Request(url, headers={"User-Agent": "CocinaRapida"})
    with urllib.request.urlopen(req, timeout=timeout, context=functions._ssl_context()) as resp, \
            open(tmp, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            data = resp.read(chunk_size)
            if not data:
                break
            f.write(data)
            digest.update(data)
            done += len(data)
            if progress:
                progress(done, total)
    if sha256 and digest.hexdigest().lower() != sha256.lower():
        os.remove(tmp)
        raise ValueError("El archivo descargado está dañado (SHA-256 no coincide).")
    os.replace(tmp, dest)
    return dest


# ---------------------------------------------------------------------------
# Android
# ---------------------------------------------------------------------------
def _activity():
    from jnius import autoclass
    return autoclass("org.kivy.android.PythonActivity").mActivity


def updates_dir():
    """Carpeta donde se guarda el APK descargado (declarada en el FileProvider)."""
    from kivy.utils import platform
    if platform == "android":
        base = _activity().getCacheDir().getAbsolutePath()
    else:
        base = os.path.join(os.path.expanduser("~"), ".cocinarapida", "cache")
    return os.path.join(base, "updates")


def clean_updates():
    """Borra APK descargados en sesiones anteriores (ya instalados o abandonados)."""
    folder = updates_dir()
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            try:
                os.remove(os.path.join(folder, name))
            except OSError:
                pass


def can_install():
    """Android 8+: ¿el usuario ha permitido a esta app instalar aplicaciones?"""
    from jnius import autoclass
    if autoclass("android.os.Build$VERSION").SDK_INT < 26:
        return True
    return bool(_activity().getPackageManager().canRequestPackageInstalls())


def open_install_permission():
    """Abre Ajustes en «Instalar apps desconocidas» para esta app."""
    from jnius import autoclass
    Intent = autoclass("android.content.Intent")
    Settings = autoclass("android.provider.Settings")
    Uri = autoclass("android.net.Uri")
    activity = _activity()
    intent = Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + activity.getPackageName()))
    activity.startActivity(intent)


def install_apk(path):
    """Abre el instalador de Android con el APK (vía FileProvider, ver build_hooks/p4a_hook.py)."""
    from jnius import autoclass
    Intent = autoclass("android.content.Intent")
    File = autoclass("java.io.File")
    FileProvider = autoclass("androidx.core.content.FileProvider")
    activity = _activity()
    uri = FileProvider.getUriForFile(activity, activity.getPackageName() + ".fileprovider", File(path))
    intent = Intent(Intent.ACTION_VIEW)
    intent.setDataAndType(uri, "application/vnd.android.package-archive")
    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK)
    activity.startActivity(intent)
