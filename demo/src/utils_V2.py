import cv2
import pickle
import numpy as np

class Park_classifier:
    """It just uses digital image process methods instead of deep learning to classify the parking space is empty or not."""

    def __init__(self, carp_park_positions_path:pickle, rect_width:int=None, rect_height:int=None):
        self.car_park_positions = self._read_positions(carp_park_positions_path) 
        self.rect_height = 48 if rect_height is None else rect_height
        self.rect_width = 107 if rect_width is None else rect_width

    def _read_positions(self, car_park_positions_path:pickle)->list:
        """It reads the pickle file for avoid any data corruption or mistake.

        Returns
        -------
        list
            List of the tuples which stores the top left point coordinates of rectangle of car park along with rotation angles. Example: [(x_1, y_1, angle), ..., [x_n, y_n, angle]]
        """
        car_park_positions = []
        try:
            car_park_positions = pickle.load(open(car_park_positions_path, 'rb'))
        except Exception as e:
            print(f"Error: {e}\n It raised while reading the car park positions file.")

        return car_park_positions

    def classify(self, image:np.ndarray, processed_image:np.ndarray, threshold:int=900)->np.ndarray:
        """It crops the already processed image into car park regions and classifies the parking space as empty or not according to threshold.

        Parameters
        ----------
        image : np.ndarray
            Original image.
        processed_image : np.ndarray
            Processed image for classification.
        threshold : int, optional
            Threshold value to classify empty spaces, by default 900.

        Returns
        -------
        np.ndarray
            Image with rectangles drawn to indicate parking space status.
        """
        empty_car_park = 0
        for x, y, angle in self.car_park_positions:
            # Defining the center for rotation
            center = (x + self.rect_width // 2, y + self.rect_height // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)

            # Create the rectangle and apply rotation
            rect = np.array([
                [x, y],
                [x + self.rect_width, y],
                [x + self.rect_width, y + self.rect_height],
                [x, y + self.rect_height]
            ], dtype=np.float32)

            rotated_rect = cv2.transform(np.array([rect]), M)[0]
            
            # Create mask for counting non-zero pixels
            mask = np.zeros_like(processed_image)
            cv2.fillPoly(mask, [np.int32(rotated_rect)], 255)
            crop = cv2.bitwise_and(processed_image, mask)

            count = cv2.countNonZero(crop)

            if count < threshold:
                empty_car_park += 1
                color, thick = (0, 255, 0), 5
            else:
                color, thick = (0, 0, 255), 2

            cv2.polylines(image, [np.int32(rotated_rect)], isClosed=True, color=color, thickness=thick)

        cv2.rectangle(image, (45, 30), (250, 75), (180, 0, 180), -1)
        ratio_text = f'Free: {empty_car_park}/{len(self.car_park_positions)}'
        cv2.putText(image, ratio_text, (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        return image

    def implement_process(self, image:np.ndarray)->np.ndarray:
        """Processes the image for classification."""
        kernel_size = np.ones((3, 3), np.uint8)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 1)
        thresholded = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        blur = cv2.medianBlur(thresholded, 5)
        dilate = cv2.dilate(blur, kernel_size, iterations=1)
        return dilate

class Coordinate_denoter:
    def __init__(self, rect_width:int=107, rect_height:int=48, car_park_positions_path:pickle="data/source/CarParkPos"):
        self.rect_width = rect_width
        self.rect_height = rect_height
        self.car_park_positions_path = car_park_positions_path
        self.car_park_positions = []

    def read_positions(self)->list:
        """Reads parking positions (x, y, angle)."""
        try:
            self.car_park_positions = pickle.load(open(self.car_park_positions_path, 'rb'))
        except FileNotFoundError:
            print("Archivo no encontrado, inicializando posiciones vacías.")
            self.car_park_positions = []
        except Exception as e:
            print(f"Error al leer posiciones: {e}")
            self.car_park_positions = []

        return self.car_park_positions

    def save_positions(self):
        """Saves parking positions (x, y, angle)."""
        try:
            with open(self.car_park_positions_path, 'wb') as f:
                pickle.dump(self.car_park_positions, f)
        except Exception as e:
            print(f"Error al guardar posiciones: {e}")

    def mouseClick(self, events:int, x:int, y:int, flags:int, params:int):
        """Handles mouse click events to add or remove parking positions."""
        if events == cv2.EVENT_LBUTTONDOWN:
            self.car_park_positions.append((x, y, 0))
            self.save_positions()

        if events == cv2.EVENT_MBUTTONDOWN:
            for index, (x1, y1, angle) in enumerate(self.car_park_positions):
                is_x_in_range = x1 <= x <= x1 + self.rect_width
                is_y_in_range = y1 <= y <= y1 + self.rect_height
                if is_x_in_range and is_y_in_range:
                    self.car_park_positions.pop(index)
                    break
            self.save_positions()

    def update_angle(self, index:int, angle:float):
        """Updates the rotation angle of a specific rectangle."""
        if 0 <= index < len(self.car_park_positions):
            x, y, _ = self.car_park_positions[index]
            self.car_park_positions[index] = (x, y, angle)
            self.save_positions()
