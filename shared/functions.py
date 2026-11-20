"""
Lógica común (sin dependencias de interfaz) para todas las apps de Cocina Rápida.

Se usa tanto en escritorio (PyInterface / RecipeManager) como en Android
(MvInterface / MvRecipeManager), por lo que sólo depende de la librería
estándar (+ certifi opcional para HTTPS en Android).
"""
import base64
import json
import os
import random
import ssl
import time
import urllib.error
import urllib.request

from i18n import _

# ---------------------------------------------------------------------------
# Constantes del proyecto
# ---------------------------------------------------------------------------
DB_REPO = "alherca25/BaseDatosRecetas"
DB_PATH = "CocinaArguinyano.json"
DB_BRANCH = "main"
DB_RAW_URL = f"https://raw.githubusercontent.com/{DB_REPO}/{DB_BRANCH}/{DB_PATH}"

FILTERS = ["Todo", "Vegetariano", "Gluten Free"]
UNITS = ["uds", "g", "mL", "cuch"]
DEFAULT_CATEGORIES = ["Sopas", "Cremas", "Verduras", "Legumbres", "Huevos", "Arroces",
                      "Pastas", "Carnes", "Pescados", "Postres", "Panes"]

HTTP_TIMEOUT = 20

# Copia de la BD incluida con las apps (primer arranque sin conexión).
LOCAL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "CocinaArguinyano.json")


# ---------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------
def _ssl_context():
    """Contexto SSL con los certificados de certifi si está disponible.

    En Android, Python no encuentra los certificados del sistema, así que sin
    certifi las peticiones HTTPS fallan con CERTIFICATE_VERIFY_FAILED.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def http_request(url, headers=None, data=None, method=None, timeout=HTTP_TIMEOUT):
    """Petición HTTP(S). Devuelve (status, bytes). Lanza urllib.error.* si falla."""
    req = urllib.request.Request(url, headers=headers or {}, data=data, method=method)
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
        return resp.status, resp.read()


def load_recipes(source_path, is_local=False):
    """Carga el recetario JSON desde un archivo local o una URL."""
    if is_local:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"No se encontró el archivo {source_path}")
        with open(source_path, "r", encoding="utf-8") as f:
            return json.load(f)
    _, body = http_request(source_path)
    return json.loads(body.decode("utf-8"))


def _api_url(path):
    return f"https://api.github.com/repos/{DB_REPO}/contents/{path}?ref={DB_BRANCH}"


def _raw_url(path):
    return f"https://raw.githubusercontent.com/{DB_REPO}/{DB_BRANCH}/{path}"


DB_API_URL = _api_url(DB_PATH)


def download_json(path=DB_PATH):
    """Descarga la versión más reciente de un JSON de BaseDatosRecetas.

    raw.githubusercontent.com guarda el archivo en caché 5 minutos, así que primero
    se usa la API de GitHub (siempre al día). Si la API falla (p. ej. límite de 60
    peticiones/hora por IP sin token), se usa la URL raw con un parámetro que evita
    la caché.
    """
    try:
        _, body = http_request(_api_url(path), headers={
            "Accept": "application/vnd.github.raw+json", "User-Agent": "CocinaRapida"})
        return json.loads(body.decode("utf-8"))
    except Exception as exc:
        print(f"API de GitHub no disponible ({exc}); se usa la URL raw")
    _, body = http_request(f"{_raw_url(path)}?t={int(time.time())}",
                           headers={"Cache-Control": "no-cache"})
    return json.loads(body.decode("utf-8"))


def download_recipes():
    return download_json(DB_PATH)


def load_recipes_with_cache(cache_path=None, fallback_paths=(), repo_path=DB_PATH):
    """Descarga un JSON de GitHub; si falla usa la caché y después copias locales.

    Devuelve (datos, origen) donde origen es "online", "cache" o "local".
    Lanza RuntimeError si no hay ninguna fuente disponible.
    """
    try:
        db = download_recipes() if repo_path == DB_PATH else download_json(repo_path)
        if cache_path:
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(db, f, ensure_ascii=False)
            except OSError as exc:
                print(f"No se pudo escribir la caché: {exc}")
        return db, "online"
    except Exception as exc:
        print(f"Descarga fallida: {exc}")

    for path, origin in [(cache_path, "cache")] + [(p, "local") for p in fallback_paths]:
        if path and os.path.exists(path):
            try:
                return load_recipes(path, is_local=True), origin
            except Exception as exc:
                print(f"No se pudo leer {path}: {exc}")
    raise RuntimeError("Sin conexión y sin copia local de las recetas.")


# ---------------------------------------------------------------------------
# GitHub API (para el gestor de recetas)
# ---------------------------------------------------------------------------
class GitHubError(Exception):
    pass


class GitHubConflict(GitHubError):
    """El archivo cambió en GitHub desde que se cargó."""


def _gh_headers(token):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "CocinaRapida"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _gh_error_message(exc):
    try:
        return json.loads(exc.read().decode("utf-8")).get("message", str(exc))
    except Exception:
        return str(exc)


def github_check_access(token, repo=DB_REPO):
    """Comprueba que el token es válido y que su usuario puede escribir en el repositorio.

    Devuelve el login del usuario. Lanza GitHubError con un mensaje claro si no hay acceso.
    (Con tokens «fine-grained», que el token tenga permiso Contents: write se comprueba al guardar.)
    """
    if not token:
        raise GitHubError("Introduce un token.")
    try:
        _, body = http_request(f"https://api.github.com/repos/{repo}", headers=_gh_headers(token))
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise GitHubError("Token inválido o caducado.") from exc
        if exc.code in (403, 404):
            raise GitHubError("Este token no tiene acceso a la base de datos de recetas.") from exc
        raise GitHubError(f"GitHub {exc.code}: {_gh_error_message(exc)}") from exc
    perms = json.loads(body.decode("utf-8")).get("permissions") or {}
    if not (perms.get("push") or perms.get("admin") or perms.get("maintain")):
        raise GitHubError("Tu usuario no tiene permiso de escritura en la base de datos de recetas.")
    try:
        _, user = http_request("https://api.github.com/user", headers=_gh_headers(token))
        return json.loads(user.decode("utf-8")).get("login", "")
    except Exception:
        return ""


def github_get_json(token=None, repo=DB_REPO, path=DB_PATH, branch=DB_BRANCH):
    """Lee el JSON y su sha mediante la API de GitHub. Devuelve (datos, sha)."""
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"
    try:
        _, body = http_request(url, headers=_gh_headers(token))
    except urllib.error.HTTPError as exc:
        raise GitHubError(f"GitHub {exc.code}: {_gh_error_message(exc)}") from exc
    meta = json.loads(body.decode("utf-8"))
    if meta.get("content"):
        raw = base64.b64decode(meta["content"])
    else:  # archivos > 1 MB: la API no incluye el contenido
        _, raw = http_request(meta["download_url"], headers=_gh_headers(token))
    return json.loads(raw.decode("utf-8")), meta["sha"]


def github_put_json(token, data, sha, message, repo=DB_REPO, path=DB_PATH, branch=DB_BRANCH):
    """Sube el JSON. Usa `sha` para no pisar cambios ajenos. Devuelve el nuevo sha."""
    if not token:
        raise GitHubError("Falta el token de GitHub.")
    content = json.dumps(data, indent=4, ensure_ascii=False).encode("utf-8")
    payload = {"message": message, "content": base64.b64encode(content).decode("ascii"),
               "branch": branch, "sha": sha}
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = dict(_gh_headers(token), **{"Content-Type": "application/json"})
    try:
        _, body = http_request(url, headers=headers, method="PUT",
                               data=json.dumps(payload).encode("utf-8"))
    except urllib.error.HTTPError as exc:
        msg = _gh_error_message(exc)
        if exc.code == 409 or (exc.code == 422 and "sha" in msg.lower()):
            raise GitHubConflict("La base de datos ha cambiado en GitHub. Recarga y vuelve a intentarlo.") from exc
        if exc.code in (401, 403):
            raise GitHubError(f"Token sin permisos o inválido ({exc.code}): {msg}") from exc
        raise GitHubError(f"GitHub {exc.code}: {msg}") from exc
    return json.loads(body.decode("utf-8"))["content"]["sha"]


# ---------------------------------------------------------------------------
# Recetas
# ---------------------------------------------------------------------------
def normalize_recipe(recipe):
    """Devuelve una copia con el formato canónico (filtros anidados, strings)."""
    filtros = dict(recipe.get("filtros") or {})
    for key in ("vegetariano", "gluten_free"):  # formato antiguo del gestor móvil
        if key in recipe and key not in filtros:
            filtros[key] = bool(recipe[key])
    return {
        "nombre": str(recipe.get("nombre", "")).strip(),
        "pagina": format_page(recipe.get("pagina", "")),
        "elaboracion": str(recipe.get("elaboracion", "")).strip(),
        "filtros": {"vegetariano": bool(filtros.get("vegetariano", False)),
                    "gluten_free": bool(filtros.get("gluten_free", False))},
        "ingredientes": [
            {"nombre": str(i.get("nombre", "")).strip(),
             "cantidad": str(i.get("cantidad", "")).strip(),
             "unidad": str(i.get("unidad", "")).strip()}
            for i in recipe.get("ingredientes", []) if str(i.get("nombre", "")).strip()
        ],
    }


def filter_recipes(recipes_list, active_filter):
    """Filtra recetas: active_filter es "Todo", "Vegetariano" o "Gluten Free"."""
    if active_filter in (None, "", "Todo"):
        return list(recipes_list)
    key = {"Vegetariano": "vegetariano", "Gluten Free": "gluten_free"}.get(active_filter)
    if key is None:
        return list(recipes_list)
    return [r for r in recipes_list if (r.get("filtros") or {}).get(key, r.get(key, False))]


def count_available(recipes_db, category, active_filter):
    return len(filter_recipes(recipes_db.get(category, []), active_filter))


def select_random_dishes(recipes_db, category, amount, active_filter):
    """Selecciona `amount` recetas al azar sin repetición.

    Devuelve (lista, limitado) donde limitado indica que había menos de las pedidas.
    """
    if category not in recipes_db:
        return [], False
    valid = filter_recipes(recipes_db[category], active_filter)
    limited = len(valid) < amount
    amount = min(amount, len(valid))
    if amount <= 0:
        return [], limited
    return random.sample(valid, amount), limited


def build_menu(recipes_db, selection, active_filter):
    """selection = {categoría: cantidad}. Devuelve lista de recetas con clave "Tipo"."""
    menu = []
    for category, qty in selection.items():
        dishes, _ = select_random_dishes(recipes_db, category, int(qty), active_filter)
        for d in dishes:
            item = dict(d)
            item["Tipo"] = category
            menu.append(item)
    return menu


# ---------------------------------------------------------------------------
# Formato
# ---------------------------------------------------------------------------
def parse_quantity(value):
    """Convierte "1", "0.5", "1,5" en float. Devuelve None si no es numérico."""
    text = str(value if value is not None else "").strip().replace(",", ".")
    if not text or text.lower() == "nan":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def format_quantity(value):
    """1.0 -> "1", 0.5 -> "0.5", texto -> texto."""
    num = parse_quantity(value) if not isinstance(value, (int, float)) else float(value)
    if num is None:
        text = str(value if value is not None else "").strip()
        return "" if text.lower() == "nan" else text
    if num.is_integer():
        return str(int(num))
    return f"{num:.2f}".rstrip("0").rstrip(".")


def format_page(value):
    """Las páginas migradas desde Excel vienen como "185.0": se muestran como "185"."""
    text = str(value if value is not None else "").strip()
    if not text or text.lower() == "nan":
        return ""
    num = parse_quantity(text)
    return format_quantity(num) if num is not None else text


def format_ingredient(ing):
    """{"nombre": "Tomate", "cantidad": "2", "unidad": "uds"} -> "2 uds Tomate"."""
    nombre = str(ing.get("nombre", "")).strip()
    unidad = str(ing.get("unidad", "")).strip()
    prefix = " ".join(p for p in (format_quantity(ing.get("cantidad", "")),
                                  _(unidad) if unidad else "") if p and p != "nan")
    return f"{prefix} {nombre}".strip() if prefix else nombre


def aggregate_ingredients(dishes):
    """Agrupa ingredientes repetidos (mismo nombre y unidad) sumando cantidades.

    Devuelve una lista ordenada de dicts {"nombre", "cantidad", "unidad"} (strings).
    Si un mismo ingrediente tiene cantidades no numéricas, se conservan aparte.
    """
    grouped = {}
    for recipe in dishes:
        for ing in recipe.get("ingredientes", []):
            nombre = str(ing.get("nombre", "")).strip()
            if not nombre:
                continue
            unidad = str(ing.get("unidad", "")).strip()
            qty = parse_quantity(ing.get("cantidad", ""))
            key = (nombre.lower(), unidad.lower(), qty is None)
            entry = grouped.setdefault(key, {"nombre": nombre, "unidad": unidad,
                                             "total": 0.0, "texts": [],
                                             "_id": ing.get("_id", "")})
            if qty is None:
                text = str(ing.get("cantidad", "")).strip()
                if text and text.lower() != "nan" and text not in entry["texts"]:
                    entry["texts"].append(text)
            else:
                entry["total"] += qty

    result = []
    for (_, _, is_text), e in grouped.items():
        cantidad = ", ".join(e["texts"]) if is_text else format_quantity(e["total"])
        item = {"nombre": e["nombre"], "cantidad": cantidad, "unidad": e["unidad"]}
        if e["_id"]:  # nombre original (español) si la receta estaba traducida
            item["_id"] = e["_id"]
        result.append(item)
    result.sort(key=lambda x: (x["nombre"].lower(), x["unidad"]))
    return result


def menu_to_text(dishes, title="Menú"):
    """Texto plano de las recetas, apto para compartir."""
    lines = [title.upper(), ""]
    for d in dishes:
        lines.append(f"* {d.get('nombre', '')}")
        meta = _(d.get("Tipo", "")) if d.get("Tipo") else ""
        page = format_page(d.get("pagina", ""))
        if page:
            meta += " · " + _("pág. {page}").format(page=page)
        if meta:
            lines.append(f"  {meta}")
        lines.append("  " + _("Ingredientes") + ":")
        lines += [f"   - {format_ingredient(i)}" for i in d.get("ingredientes", [])]
        elab = str(d.get("elaboracion", "")).strip()
        if elab:
            lines += ["  " + _("Elaboración") + ":", "  " + elab.replace("\n", "\n  ")]
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def item_key(item):
    """Clave estable de un ingrediente de la lista de la compra.

    Usa el nombre original en español ("_id") si existe, para que lo marcado no se
    pierda al cambiar de idioma.
    """
    name = item.get("_id") or item.get("nombre", "")
    return f"{name.strip().lower()}|{item.get('unidad', '').strip()}"


def shopping_to_text(items, title="Lista de la compra", checked=()):
    """Texto plano de la lista de la compra; los ya marcados se omiten."""
    lines = [title.upper(), ""]
    for it in items:
        if item_key(it) in checked:
            continue
        qty = " ".join(p for p in (it.get("cantidad", ""), _(it.get("unidad", "")) if it.get("unidad") else "") if p)
        lines.append(f"[ ] {it['nombre']}" + (f" — {qty}" if qty else ""))
    return "\n".join(lines).strip() + "\n"
