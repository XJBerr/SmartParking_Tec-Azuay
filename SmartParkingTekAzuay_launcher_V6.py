import sys
import subprocess
import webbrowser
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QUrl

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.setWindowTitle("Smart Parking Tec - Azuay")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('static/img/lglauncher.jpeg'))

        # Centrar la ventana en la pantalla
        self.center()

        # Cargar imagen de fondo
        self.background_label = QLabel(self)
        self.background_image = QPixmap('static/img/fondo.jpeg')
        self.background_label.setPixmap(self.background_image)
        self.background_label.setScaledContents(True)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.raise_()  # Asegura que el fondo esté detrás de otros widgets

        # Layout principal
        main_layout = QVBoxLayout(self)

        # Título
        title_label = QLabel("Smart Parking Tec - Azuay")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        main_layout.addWidget(title_label)

        # Texto de bienvenida
        welcome_label = QLabel("¡Te invitamos a explorar nuestro nuevo programa!")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("font-size: 18px; color: white;")
        main_layout.addWidget(welcome_label)

        # Espaciador
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Layout de botones
        button_layout = QHBoxLayout()

        # Botones
        btn_demo_test = QPushButton("Ejecutar el visualizador del parqueadero")
        btn_demo_test.setStyleSheet("font-size: 16px; padding: 10px;")
        btn_demo_test.clicked.connect(self.run_demo_test)
        button_layout.addWidget(btn_demo_test)

        btn_coordinate_generator = QPushButton("Ejecutar el editor de Coordenadas")
        btn_coordinate_generator.setStyleSheet("font-size: 16px; padding: 10px;")
        btn_coordinate_generator.clicked.connect(self.run_coordinate_generator)
        button_layout.addWidget(btn_coordinate_generator)

        main_layout.addLayout(button_layout)

        # Espaciador
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Botón de salir
        btn_exit = QPushButton("Salir")
        btn_exit.setStyleSheet("font-size: 16px; padding: 10px;")
        btn_exit.clicked.connect(self.close)
        main_layout.addWidget(btn_exit, alignment=Qt.AlignCenter)

        # Enlace a redes sociales
        social_label = QLabel('<a href="https://www.facebook.com/share/162UzfTbw6/" style="color: lightblue;">Visita nuestras redes sociales</a>')
        social_label.setOpenExternalLinks(True)
        social_label.setAlignment(Qt.AlignCenter)
        social_label.setStyleSheet("font-size: 16px; color: white; text-decoration: none;")
        main_layout.addWidget(social_label)

        self.setLayout(main_layout)

    def center(self):
        # Centrar la ventana en la pantalla
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def resizeEvent(self, event):
        # Ajustar el tamaño del fondo cuando la ventana cambia de tamaño
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def run_demo_test(self):
        subprocess.run(['python', 'demo_test_V10_4.py'])

    def run_coordinate_generator(self):
        subprocess.run(['python', 'Car_Parking_Coordinate_Generator_V33.py'])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())