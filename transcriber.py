import subprocess
import os
import torch
from PySide6.QtCore import QObject, Signal

class TranscriberWorker(QObject):
    finished = Signal()
    progress = Signal(int)
    status_update = Signal(str)
    error = Signal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.is_running = True

    def run(self):
        try:
            # 1. Detectar dispositivo (CUDA o CPU)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            fp16 = "True" if device == "cuda" else "False"
            self.status_update.emit(f"Dispositivo detectado: {device.upper()}. Usando precisión FP16: {fp16}.")
            
            total_files = len(self.params["files"])
            for i, audio_file in enumerate(self.params["files"]):
                if not self.is_running:
                    break

                self.status_update.emit(f"Procesando archivo {i+1}/{total_files}: {os.path.basename(audio_file)}")
                self.progress.emit(0)

                # 2. Construir el comando para Whisper con idioma fijo
                command = [
                    "whisper",
                    f'"{audio_file}"',
                    "--model", self.params["model"],
                    "--language", "Spanish", # Idioma fijado aquí
                    "--device", device,
                    "--fp16", fp16,
                    "--model_dir", f'"{self.params["models_dir"]}"',
                    "--output_dir", f'"{self.params["output_dir"]}"',
                    "--output_format", "all"
                ]

                # Usamos shell=True en Windows para manejar correctamente las rutas con espacios
                # CREATE_NO_WINDOW evita que aparezca una consola por cada llamada
                process = subprocess.Popen(" ".join(command), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=0x08000000)

                # 3. Leer la salida en tiempo real. Para un progreso real, habría que parsear
                # la salida de la barra de progreso de Whisper, que es compleja.
                # Aquí simulamos un avance simple por archivo completado.
                process.wait()
                
                if process.returncode != 0:
                    output = process.stdout.read()
                    raise RuntimeError(f"Error al transcribir '{os.path.basename(audio_file)}':\n{output}")

                self.progress.emit(int((i + 1) / total_files * 100))
            
            self.status_update.emit("Proceso finalizado.")

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def stop(self):
        self.is_running = False