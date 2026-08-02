# main.py
# Punto de entrada para Buildozer (compilación Android).
# Buildozer busca SIEMPRE un archivo llamado "main.py" en la raíz del proyecto.
# Toda la lógica e interfaz viven en MvInterface.py.

from MvInterface import CocinaApp

if __name__ == "__main__":
    CocinaApp().run()
