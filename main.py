import sys
import os
from PySide6.QtWidgets import QApplication
from gui import MainWindow

# --- Funciones para el entorno portable ---
def get_base_path():
    """ Obtiene la ruta base del ejecutable para encontrar los recursos. """
    if getattr(sys, 'frozen', False):
        # Estamos en un ejecutable de PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # Estamos ejecutando como script .py
        return os.path.dirname(os.path.abspath(__file__))

def setup_environment(base_path):
    """ Añade FFmpeg a la variable de entorno PATH de forma temporal. """
    ffmpeg_path = os.path.join(base_path, 'ffmpeg', 'bin')
    if os.path.isdir(ffmpeg_path):
        os.environ['PATH'] = ffmpeg_path + os.pathsep + os.environ['PATH']
        print(f"INFO: FFmpeg añadido al PATH temporal: {ffmpeg_path}")
    else:
        print("ADVERTENCIA: Carpeta de FFmpeg no encontrada.")

if __name__ == "__main__":
    # 1. Obtener la ruta base de la aplicación
    base_dir = get_base_path()
    
    # 2. Configurar el entorno (añadir FFmpeg al PATH)
    setup_environment(base_dir)
    
    # 3. Iniciar la aplicación Qt
    app = QApplication(sys.argv)
    window = MainWindow(base_dir)
    window.show()
    
    sys.exit(app.exec())