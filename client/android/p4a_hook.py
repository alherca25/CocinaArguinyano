"""Hook de python-for-android para el Recetario (lo usa buildozer.spec: p4a.hook).

Añade un FileProvider al AndroidManifest para que la app pueda pasar el APK
descargado al instalador de Android (desde Android 7 no se permiten rutas file://).

Se ejecuta en la carpeta de la distribución, después de generar el manifiesto y
antes de que Gradle empaquete el APK.
"""
import os

PROVIDER = """
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/cocina_file_paths" />
        </provider>
"""

PATHS = """<?xml version="1.0" encoding="utf-8"?>
<paths>
    <cache-path name="updates" path="updates/" />
</paths>
"""


def after_apk_build(toolchain):
    manifest = os.path.join("src", "main", "AndroidManifest.xml")
    with open(manifest, encoding="utf-8") as f:
        xml = f.read()
    if "androidx.core.content.FileProvider" not in xml:
        if "</application>" not in xml:
            raise RuntimeError("p4a_hook: no se encontró </application> en el manifiesto")
        xml = xml.replace("</application>", PROVIDER + "    </application>", 1)
        with open(manifest, "w", encoding="utf-8") as f:
            f.write(xml)
    res_xml = os.path.join("src", "main", "res", "xml")
    os.makedirs(res_xml, exist_ok=True)
    with open(os.path.join(res_xml, "cocina_file_paths.xml"), "w", encoding="utf-8") as f:
        f.write(PATHS)
    print("p4a_hook: FileProvider añadido al manifiesto")
