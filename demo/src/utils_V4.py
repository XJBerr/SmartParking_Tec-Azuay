import json
import cv2
import numpy as np


class Park_classifier:
    """Clasifica espacios de estacionamiento como libres u ocupados basándose en procesamiento de imágenes."""

    def __init__(self, carp_park_positions_path: str, rect_width: int = 50, rect_height: int = 30):
        self.car_park_positions = self._read_positions(carp_park_positions_path)
        self.rect_width = rect_width
        self.rect_height = rect_height

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

    def classify(self, image: np.ndarray, processed_image: np.ndarray, threshold: int = 900) -> np.ndarray:
        """Clasifica los espacios de estacionamiento como libres u ocupados.

        Args:
            image (np.ndarray): Imagen original.
            processed_image (np.ndarray): Imagen procesada.
            threshold (int, optional): Valor umbral para determinar si un espacio está ocupado. Por defecto 900.

        Returns:
            np.ndarray: Imagen con los resultados de la clasificación dibujados.
        """
        empty_car_park = 0

        for pos in self.car_park_positions:
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
            else:
                color, thickness = (0, 0, 255), 2  # Rojo para espacio ocupado

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

    def implement_process(self, image: np.ndarray) -> np.ndarray:
        """Procesa la imagen para preparar la clasificación."""
        kernel_size = np.ones((3, 3), np.uint8)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 1)
        thresholded = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        blur = cv2.medianBlur(thresholded, 5)
        dilate = cv2.dilate(blur, kernel_size, iterations=1)
        return dilate
