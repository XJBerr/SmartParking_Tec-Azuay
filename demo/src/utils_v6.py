import json
import cv2
import numpy as np
import mysql.connector
from datetime import datetime, timedelta


class ParkingDatabaseManager:
    """Clase para manejar la conexión y las operaciones con la base de datos MySQL."""

    def __init__(self, host, user, password, database):
        """Inicializa la conexión a la base de datos."""
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            if self.connection.is_connected():
                print("Conexión exitosa a la base de datos.")
        except mysql.connector.Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            self.connection = None

    def close_connection(self):
        """Cierra la conexión a la base de datos."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión cerrada.")

    def insert_parking_record(self, parking_spaces_id, hora_llegada):
        """Inserta un registro de entrada en la tabla parking_records."""
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO parking_records (parking_spaces_id, hora_llegada)
                VALUES (%s, %s)
            """
            cursor.execute(query, (parking_spaces_id, hora_llegada))
            self.connection.commit()
            print(f"Registro de entrada insertado para el espacio {parking_spaces_id}.")
        except mysql.connector.Error as e:
            print(f"Error al insertar registro de entrada en la base de datos: {e}")

    def update_parking_record(self, parking_spaces_id, hora_salida):
        """Actualiza un registro existente con la hora de salida y calcula la duración."""
        try:
            cursor = self.connection.cursor()
            query = """
                UPDATE parking_records
                SET hora_salida = %s, duracion = TIMEDIFF(%s, hora_llegada)
                WHERE parking_spaces_id = %s AND hora_salida IS NULL
            """
            cursor.execute(query, (hora_salida, hora_salida, parking_spaces_id))
            self.connection.commit()
            print(f"Registro actualizado para el espacio {parking_spaces_id} con hora de salida.")
        except mysql.connector.Error as e:
            print(f"Error al actualizar registro en la base de datos: {e}")

    def update_space_status(self, parking_spaces_id, estado):
        """Actualiza el estado de un espacio en la tabla state_date."""
        try:
            cursor = self.connection.cursor()
            fecha_actual = datetime.now().date()
            hora_actual = datetime.now().time()
            query = """
                INSERT INTO state_date (parking_spaces_id_sd, fecha, estado, hora_cambio)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (parking_spaces_id, fecha_actual, estado, hora_actual))
            self.connection.commit()
            print(f"Estado del espacio {parking_spaces_id} actualizado a '{estado}'.")
        except mysql.connector.Error as e:
            print(f"Error al actualizar el estado del espacio: {e}")


class Park_classifier:
    """Clasifica espacios de estacionamiento como libres u ocupados basándose en procesamiento de imágenes."""

    def __init__(self, carp_park_positions_path: str, rect_width: int = 50, rect_height: int = 30):
        self.car_park_positions = self._read_positions(carp_park_positions_path)
        self.rect_width = rect_width
        self.rect_height = rect_height

        # Inicialización del gestor de la base de datos
        self.db_manager = ParkingDatabaseManager(
            host="localhost",
            user="root",
            password="",
            database="car_parking"
        )
        self.espacios_ocupados = {}  # Diccionario para registrar ocupaciones y salidas de espacios

    def _read_positions(self, carp_park_positions_path: str) -> list:
        """Lee las posiciones de los espacios de estacionamiento desde un archivo JSON."""
        try:
            with open(carp_park_positions_path, "r") as f:
                data = json.load(f)
                return [(pos["x"], pos["y"], pos["angle"], pos["width"], pos["height"]) for pos in data]
        except FileNotFoundError:
            print(f"Archivo '{carp_park_positions_path}' no encontrado. Inicializando lista vacía.")
            return []
        except Exception as e:
            print(f"Error al leer las posiciones: {e}")
            return []

    def classify(self, image: np.ndarray, processed_image: np.ndarray, threshold: int = 500) -> np.ndarray:
        """Clasifica los espacios de estacionamiento como libres u ocupados."""
        empty_car_park = 0

        for idx, pos in enumerate(self.car_park_positions, start=1):
            x, y, angle, width, height = pos

            # Definir el centro de rotación
            center = (x + width // 2, y + height // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)

            # Crear el rectángulo y aplicar la rotación
            rect = np.array([
                [x, y],
                [x + width, y],
                [x + width, y + height],
                [x, y + height]
            ], dtype=np.float32)

            rotated_rect = cv2.transform(np.array([rect]), M)[0]

            # Crear máscara para contar píxeles no nulos
            mask = np.zeros_like(processed_image)
            cv2.fillPoly(mask, [np.int32(rotated_rect)], 255)
            crop = cv2.bitwise_and(processed_image, mask)

            count = cv2.countNonZero(crop)

            if count < threshold:
                empty_car_park += 1
                color, thickness = (0, 255, 0), 2  # Verde para espacio libre

                # Registrar salida si estaba ocupado
                if idx in self.espacios_ocupados:
                    hora_llegada = self.espacios_ocupados.pop(idx)
                    hora_salida = datetime.now()
                    self.db_manager.update_parking_record(idx, hora_salida)
                    self.db_manager.update_space_status(idx, "Libre")
            else:
                color, thickness = (0, 0, 255), 2  # Rojo para espacio ocupado

                # Registrar entrada si estaba libre
                if idx not in self.espacios_ocupados:
                    self.espacios_ocupados[idx] = datetime.now()
                    self.db_manager.insert_parking_record(idx, self.espacios_ocupados[idx])
                    self.db_manager.update_space_status(idx, "Ocupado")

            # Dibujar el rectángulo rotado en la imagen original
            cv2.polylines(image, [np.int32(rotated_rect)], isClosed=True, color=color, thickness=thickness)

        # Agregar indicador de espacios libres y ocupados
        self._draw_indicator(image, empty_car_park)

        return image

    def _draw_indicator(self, image: np.ndarray, empty_car_park: int):
        """Dibuja un indicador en la esquina superior izquierda mostrando espacios libres y ocupados."""
        total_spaces = len(self.car_park_positions)

        # Dibujo del rectángulo de la leyenda
        cv2.rectangle(image, (45, 30), (250, 75), (180, 0, 180), -1)

        # Texto con la cantidad de espacios libres y ocupados
        ratio_text = f'Free: {empty_car_park}/{total_spaces}'
        cv2.putText(image, ratio_text, (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    def handle_exit(self):
        """Registra la salida de todos los espacios ocupados al cerrar el programa."""
        hora_salida = datetime.now() - timedelta(seconds=1)  # Restar un segundo para evitar inconsistencias
        for idx in list(self.espacios_ocupados.keys()):
            self.db_manager.update_parking_record(idx, hora_salida)
            self.db_manager.update_space_status(idx, "Libre")
            self.espacios_ocupados.pop(idx)

    def implement_process(self, image: np.ndarray) -> np.ndarray:
        """Procesa la imagen para preparar la clasificación."""
        kernel_size = np.ones((3, 3), np.uint8)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 1)
        thresholded = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        blur = cv2.medianBlur(thresholded, 5)
        dilate = cv2.dilate(blur, kernel_size, iterations=1)
        return dilate
