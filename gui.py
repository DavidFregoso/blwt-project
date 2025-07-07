import os
import json
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QComboBox, QLineEdit,
                               QFileDialog, QProgressBar, QListWidget,
                               QMessageBox)
from transcriber import TranscriberWorker

class MainWindow(QMainWindow):
    def __init__(self, base_path):
        super().__init__()
        self.base_path = base_path
        self.config = self.load_config()
        self.audio_files = []

        self.setWindowTitle("Blueberries Lab Whisper Transcriber (BL-WT)")
        self.setMinimumSize(600, 400)

        # --- Layouts ---
        main_layout = QVBoxLayout()
        file_selection_layout = QHBoxLayout()
        options_layout = QHBoxLayout()
        output_layout = QHBoxLayout()

        # --- Widgets ---
        # 1. Selección de archivos
        self.file_list_widget = QListWidget()
        self.file_list_widget.setFixedHeight(100)
        select_files_button = QPushButton("1. Seleccionar Audios (.mp3, .wav, .m4a)")

        # 2. Opciones
        model_label = QLabel("2. Elegir Calidad:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["small", "medium", "large"])
        self.model_combo.setCurrentText(self.config.get("default_model", "medium"))

        # 3. Carpeta de salida
        output_label = QLabel("3. Carpeta de Salida:")
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Seleccione una carpeta...")
        self.output_path_edit.setReadOnly(True)
        select_output_button = QPushButton("...")

        # 4. Iniciar y Progreso
        self.start_button = QPushButton("Iniciar Transcripción")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("Listo.")
        self.status_label.setAlignment(Qt.AlignCenter)

        # --- Composición de la Interfaz ---
        file_selection_layout.addWidget(self.file_list_widget)
        file_selection_layout.addWidget(select_files_button)

        options_layout.addWidget(model_label)
        options_layout.addWidget(self.model_combo)
        options_layout.addStretch()

        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(select_output_button)

        main_layout.addLayout(file_selection_layout)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(output_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.start_button)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.status_label)

        # Menú "Acerca de"
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Ayuda")
        about_action = help_menu.addAction("Acerca de BL-WT")
        about_action.triggered.connect(self.show_about_dialog)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- Conexiones de Señales ---
        select_files_button.clicked.connect(self.select_audio_files)
        select_output_button.clicked.connect(self.select_output_folder)
        self.start_button.clicked.connect(self.start_transcription)

    def load_config(self):
        config_path = os.path.join(self.base_path, 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def show_about_dialog(self):
        license_path = os.path.join(self.base_path, 'license.txt')
        try:
            with open(license_path, 'r', encoding='utf-8') as f:
                about_text = f.read()
        except FileNotFoundError:
            about_text = "© 2025 Blueberries Lab.\nLicencia no encontrada."
        QMessageBox.about(self, "Acerca de BL-WT", about_text)

    def select_audio_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos de audio", "", "Archivos de Audio (*.mp3 *.wav *.m4a)")
        if files:
            self.audio_files = files
            self.file_list_widget.clear()
            self.file_list_widget.addItems([os.path.basename(f) for f in files])
            self.status_label.setText(f"{len(files)} archivo(s) seleccionado(s).")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida")
        if folder:
            self.output_path_edit.setText(folder)
            
    def set_controls_enabled(self, enabled):
        self.start_button.setEnabled(enabled)
        self.model_combo.setEnabled(enabled)
        
    def start_transcription(self):
        # Validaciones
        if not self.audio_files:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona al menos un archivo de audio.")
            return
        if not self.output_path_edit.text():
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona una carpeta de salida.")
            return

        self.set_controls_enabled(False)
        self.status_label.setText("Iniciando transcripción...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        params = {
            "files": self.audio_files,
            "model": self.model_combo.currentText(),
            "output_dir": self.output_path_edit.text(),
            "models_dir": os.path.join(self.base_path, 'whisper_models')
        }

        self.thread = QThread()
        self.worker = TranscriberWorker(params)
        self.worker.moveToThread(self.thread)

        # Conexiones
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status_update.connect(self.status_label.setText)
        self.worker.error.connect(self.on_process_error)
        
        self.thread.start()

    def on_process_finished(self):
        self.thread.quit()
        self.thread.wait()
        self.set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("¡Proceso completado con éxito!")
        QMessageBox.information(self, "Éxito", "Todos los archivos han sido transcritos.")

    def on_process_error(self, message):
        self.thread.quit()
        self.thread.wait()
        self.set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ocurrió un error.")
        QMessageBox.critical(self, "Error", message)