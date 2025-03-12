from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QEvent, QSize, QTimer, QObject
from PyQt6.QtGui import QPalette, QColor, QIcon
import shutil
import os
import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from styles import apply_stylesheet

# Define file categories
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif"],
    "Documents": [".pdf", ".docx", ".txt"],
    "Videos": [".mp4", ".mkv"],
    "Executables": [".exe"],
    "Archives": [".zip", ".rar"]
}

class FileHandler(QObject, FileSystemEventHandler):
    file_moved = pyqtSignal(str, str)

    def __init__(self, source_folder):
        super().__init__()
        self.source_folder = source_folder

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()

            for category, extensions in FILE_CATEGORIES.items():
                if file_ext in extensions:
                    dest_folder = os.path.join(self.source_folder, category)
                    os.makedirs(dest_folder, exist_ok=True)
                    new_path = os.path.join(dest_folder, file_name)
                    try:
                        shutil.move(file_path, new_path)
                        self.file_moved.emit(file_name, category)
                    except Exception as e:
                        print(f"Error moving file {file_name}: {e}")
                    return

class FolderMonitor(QThread):
    file_moved = pyqtSignal(str, str)

    def __init__(self, source_folder):
        super().__init__()
        self.source_folder = source_folder
        self.stop_event = False
        self.observer = None

    def run(self):
        print(f"Starting monitor for {self.source_folder}")
        event_handler = FileHandler(self.source_folder)
        event_handler.file_moved.connect(self.file_moved)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.source_folder, recursive=True)
        self.observer.start()
        try:
            while not self.stop_event:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Keyboard interrupt received")
        finally:
            self.observer.stop()
            self.observer.join()
        print("Monitor stopped")

    def stop(self):
        print("Stopping monitor")
        self.stop_event = True
        if self.observer:
            self.observer.stop()
            self.observer.join()

class FileOrganizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart File Organizer")
        self.setGeometry(400, 200, 600, 700)
        self.is_dark_mode = False

        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Top layout for header and toggle button
        self.top_layout = QHBoxLayout()
        self.header_label = QLabel("Smart File Organizer")
        self.header_label.setObjectName("header")
        self.top_layout.addWidget(self.header_label)
        self.top_layout.addStretch()  # Push toggle button to the right
        self.toggle_dark_mode_button = QPushButton()
        self.toggle_dark_mode_button.setObjectName("toggleDarkModeButton")
        self.toggle_dark_mode_button.setIcon(QIcon("icons/sun-line.png"))
        self.toggle_dark_mode_button.setIconSize(QSize(24, 24))
        self.top_layout.addWidget(self.toggle_dark_mode_button)
        self.layout.addLayout(self.top_layout)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setObjectName("logOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("opacity: 0;")
        self.layout.addWidget(self.log_output)

        # Button Container (Bottom)
        self.button_container = QFrame()
        self.button_container.setObjectName("buttonContainer")
        self.button_container.setStyleSheet("opacity: 0;")
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the buttons
        self.button_layout.setSpacing(8)  # Tighter spacing like Stripe

        self.select_button = QPushButton("Select Folder")
        self.start_button = QPushButton("Start Monitoring")
        self.stop_button = QPushButton("Stop Monitoring")
        self.view_logs_button = QPushButton("View Logs")

        buttons = [self.select_button, self.start_button, self.stop_button, self.view_logs_button]
        for button in buttons:
            self.button_layout.addWidget(button)
        self.button_container.setLayout(self.button_layout)
        self.layout.addWidget(self.button_container)

        self.setLayout(self.layout)
        self.source_folder = None
        self.worker = None

        # Apply initial stylesheet
        apply_stylesheet(self, self.is_dark_mode)

        # Button connections
        self.select_button.clicked.connect(self.select_folder)
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.view_logs_button.clicked.connect(self.view_logs)
        self.toggle_dark_mode_button.clicked.connect(self.toggle_dark_mode)

        # Animations
        self.fade_in_animation = QPropertyAnimation(self.button_container, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.log_fade_in_animation = QPropertyAnimation(self.log_output, b"windowOpacity")
        self.log_fade_in_animation.setDuration(500)
        self.log_fade_in_animation.setStartValue(0)
        self.log_fade_in_animation.setEndValue(1)
        self.log_fade_in_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        QTimer.singleShot(100, self.start_fade_in)

        self.log_animation = QPropertyAnimation(self.log_output, b"maximumHeight")
        self.log_animation.setDuration(300)
        self.log_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        for button in buttons + [self.toggle_dark_mode_button]:
            button.installEventFilter(self)

    def start_fade_in(self):
        self.fade_in_animation.start()
        self.log_fade_in_animation.start()

    def apply_stylesheet(self):
        current_opacity = self.windowOpacity()
        apply_stylesheet(self, self.is_dark_mode)
        self.setWindowOpacity(current_opacity)
        mode_transition = QPropertyAnimation(self, b"windowOpacity")
        mode_transition.setDuration(500)
        mode_transition.setStartValue(current_opacity)
        mode_transition.setEndValue(1)
        mode_transition.setEasingCurve(QEasingCurve.Type.OutQuad)
        mode_transition.start()

    def eventFilter(self, obj, event):
        if obj in [self.select_button, self.start_button, self.stop_button, self.view_logs_button, self.toggle_dark_mode_button]:
            if event.type() == QEvent.Type.Enter:
                anim = QPropertyAnimation(obj, b"geometry")
                anim.setDuration(200)
                anim.setStartValue(obj.geometry())
                anim.setEndValue(obj.geometry().adjusted(0, 0, 0, -5))
                anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                anim.start()

                scale_anim = QPropertyAnimation(obj, b"minimumWidth")
                scale_anim.setDuration(200)
                scale_anim.setStartValue(obj.minimumWidth())
                scale_anim.setEndValue(obj.minimumWidth() * 1.05)
                scale_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                scale_anim.start()
            elif event.type() == QEvent.Type.Leave:
                anim = QPropertyAnimation(obj, b"geometry")
                anim.setDuration(200)
                anim.setStartValue(obj.geometry())
                anim.setEndValue(obj.geometry().adjusted(0, 0, 0, 5))
                anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                anim.start()

                scale_anim = QPropertyAnimation(obj, b"minimumWidth")
                scale_anim.setDuration(200)
                scale_anim.setStartValue(obj.minimumWidth())
                scale_anim.setEndValue(obj.minimumWidth() / 1.05)
                scale_anim.start()
        return super().eventFilter(obj, event)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Monitor")
        if folder:
            self.source_folder = folder
            self.log_output.append(f"📁 Folder Selected: {self.source_folder}")
            self.animate_log_with_fade()

    def organize_existing_files(self):
        """Organize existing files in the selected folder."""
        if not self.source_folder:
            return
        self.log_output.append("🗂️ Organizing existing files...")
        self.animate_log_with_fade()
        for file_name in os.listdir(self.source_folder):
            file_path = os.path.join(self.source_folder, file_name)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(file_name)[1].lower()
                for category, extensions in FILE_CATEGORIES.items():
                    if file_ext in extensions:
                        dest_folder = os.path.join(self.source_folder, category)
                        os.makedirs(dest_folder, exist_ok=True)
                        new_path = os.path.join(dest_folder, file_name)
                        try:
                            shutil.move(file_path, new_path)
                            self.log_output.append(f"✅ Moved existing file: {file_name} → {category}")
                            self.animate_log_with_fade()
                        except Exception as e:
                            self.log_output.append(f"❌ Error moving existing file {file_name}: {str(e)}")
                            self.animate_log_with_fade()
                        break

    def start_monitoring(self):
        if not self.source_folder:
            self.log_output.append("⚠️ Please select a folder first!")
            self.animate_log_with_fade()
            return
        if self.worker and self.worker.isRunning():
            self.log_output.append("⚠️ Monitoring is already running!")
            self.animate_log_with_fade()
            return
        try:
            # Organize existing files first
            self.organize_existing_files()
            # Then start monitoring for new files
            if self.worker:
                self.worker.stop()
                self.worker.wait()
            self.worker = FolderMonitor(self.source_folder)
            self.worker.file_moved.connect(self.update_log)
            self.worker.start()
            self.log_output.append("▶️ Monitoring Started...")
            self.animate_log_with_fade()
        except Exception as e:
            self.log_output.append(f"❌ Error starting monitoring: {str(e)}")
            self.animate_log_with_fade()
            print(f"Exception in start_monitoring: {e}", file=sys.stderr)

    def stop_monitoring(self):
        if self.worker and self.worker.isRunning():
            try:
                self.worker.stop()
                self.worker.wait()
                self.worker = None
                self.log_output.append("⏹️ Monitoring Stopped.")
                self.animate_log_with_fade()
            except Exception as e:
                self.log_output.append(f"❌ Error stopping monitoring: {str(e)}")
                self.animate_log_with_fade()
                print(f"Exception in stop_monitoring: {e}", file=sys.stderr)
        else:
            self.log_output.append("⚠️ No monitoring to stop!")
            self.animate_log_with_fade()

    def view_logs(self):
        os.system("notepad log.txt")

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_stylesheet()

    def update_log(self, file_name, category):
        log_entry = f"✅ Moved: {file_name} → {category}"
        self.log_output.append(log_entry)
        with open("log.txt", "a") as log_file:
            log_file.write(log_entry + "\n")
        self.animate_log_with_fade()

    def animate_log_with_fade(self):
        self.log_animation.setStartValue(self.log_output.height())
        self.log_animation.setEndValue(self.log_output.height() + 20)
        self.log_animation.start()

        log_fade = QPropertyAnimation(self.log_output, b"windowOpacity")
        log_fade.setDuration(300)
        log_fade.setStartValue(0.5)
        log_fade.setEndValue(1)
        log_fade.setEasingCurve(QEasingCurve.Type.OutQuad)
        log_fade.start()

if __name__ == "__main__":
    app = QApplication([])
    window = FileOrganizerApp()
    window.show()
    app.exec()