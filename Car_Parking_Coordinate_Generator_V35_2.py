import json
import cv2
import numpy as np
import pyperclip  # Asegúrate de tener instalada esta biblioteca
from src.utils_V2 import Coordinate_denoter

class Coordinate_denoter:
    def __init__(self):
        self.car_park_positions = []
        self.rect_width = 50
        self.rect_height = 30
        self.file_path = "positions.json"

    def read_positions(self):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                self.car_park_positions = [
                    (pos["x"], pos["y"], pos["angle"], pos["width"], pos["height"]) for pos in data
                ]
        except FileNotFoundError:
            print("Archivo de posiciones no encontrado. Se creará uno nuevo al guardar.")
        except Exception as e:
            print(f"Error al leer posiciones: {e}")

    def save_positions(self, positions, angles, widths, heights):
        try:
            data = [
                {"x": pos[0], "y": pos[1], "angle": angle, "width": width, "height": height}
                for pos, angle, width, height in zip(positions, angles, widths, heights)
            ]
            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=4)
            print("Posiciones guardadas correctamente.")
        except Exception as e:
            print(f"Error al guardar posiciones: {e}")

class CoordinateManipulator:
    def __init__(self):
        self.coordinate_generator = Coordinate_denoter()
        self.coordinate_generator.read_positions()

        self.rect_widths = []
        self.rect_heights = []
        self.rotation_angles = []

        # Inicializar camera_url aquí
        self.camera_url = ""

        if self.coordinate_generator.car_park_positions:
            self.rect_widths = [pos[3] for pos in self.coordinate_generator.car_park_positions]
            self.rect_heights = [pos[4] for pos in self.coordinate_generator.car_park_positions]
            self.rotation_angles = [pos[2] for pos in self.coordinate_generator.car_park_positions]

        self.dragging = False
        self.resizing = False
        self.selected_rect = None
        self.offset = (0, 0)

        self.menu_visible = False
        self.scroll_offset = 0
        self.COLOR_MENU = (220, 220, 220)
        self.COLOR_BOTON_FONDO = (70, 70, 70)
        self.COLOR_BOTON_TEXT = (255, 255, 255)
        self.COLOR_BOTON_BORDE = (0, 0, 0)
        self.COLOR_RECTANGULO = (0, 100, 255)
        self.COLOR_RECTANGULO_SELECCIONADO = (0, 255, 0)
        self.COLOR_TEXTO_ABAJO = (0, 128, 255)
        self.COLOR_FONDO_ABAJO = (222, 184, 135)

        self.buttons = self.create_buttons({
            "menu": "Menu",
            "quit": "Salir"
        }, start_x=10, start_y=10)

        self.edit_buttons = self.create_buttons({
            "rotate": "Rotar",
            "delete": "Eliminar",
            "add": "Agregar",
            "increase": "Aumentar",
            "decrease": "Disminuir",
            "save": "Guardar"
        }, start_x=10, start_y=60)

        self.texts = [
            "",
            "Haga clic en un rectángulo para seleccionarlo.",
            "Funciones de los botones:",
            "Rote, elimine, modifique, agregue y guarde posiciones.",
            "Teclas:",
            "R -> Rotar",
            "D -> Eliminar",
            "A -> Agregar",
            "S -> Guardar",
            "+ -> Aumentar",
            "- -> Disminuir",
            "C -> Cambiar cámara",
            "Tab -> Ingresar URL",
            "Q -> Salir"
        ]

        self.cameras = self.get_available_cameras()
        self.current_camera_index = 0
        self.cap = cv2.VideoCapture(self.cameras[self.current_camera_index])

        if not self.cap.isOpened():
            raise ValueError("No se pudo acceder a la cámara.")

        self.scroll_buttons = {}

    def create_buttons(self, button_labels, start_x, start_y, small=False):
        buttons = {}
        current_x = start_x
        for label, text in button_labels.items():
            (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
            w = 50 if small else min(max(text_width + 20, 70), 100)
            h = 20 if small else text_height + 20
            buttons[label] = (current_x, start_y, w, h)
            current_x += w + 5
        return buttons

    def get_available_cameras(self):
        available_cameras = []
        for i in range(2):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        if not available_cameras:
            raise ValueError("No se encontraron cámaras disponibles.")
        return available_cameras

    def switch_camera(self):
        self.cap.release()
        self.current_camera_index = (self.current_camera_index + 1) % len(self.cameras)
        self.cap = cv2.VideoCapture(self.cameras[self.current_camera_index])
        if not self.cap.isOpened():
            print(f"No se pudo abrir la cámara {self.cameras[self.current_camera_index]}.")

    def draw_text(self, image, text, position, font_scale=0.6, color=(255, 255, 255), thickness=2):
        x, y = position
        cv2.putText(image, text, (x - 1, y - 1), cv2.FONT_HERSHEY_COMPLEX, font_scale, (0, 0, 0), thickness + 1)
        cv2.putText(image, text, position, cv2.FONT_HERSHEY_COMPLEX, font_scale, color, thickness)

    def draw_buttons(self, image):
        for label, (x, y, w, h) in self.buttons.items():
            cv2.rectangle(image, (x, y), (x + w, y + h), self.COLOR_BOTON_FONDO, -1)
            cv2.rectangle(image, (x, y), (x + w, y + h), self.COLOR_BOTON_BORDE, 2)
            self.draw_text(image, label, (x + 10, y + (h // 2) + 5), font_scale=0.5, color=self.COLOR_BOTON_TEXT)

        if self.menu_visible:
            for label, (x, y, w, h) in self.edit_buttons.items():
                cv2.rectangle(image, (x, y), (x + w, y + h), self.COLOR_BOTON_FONDO, -1)
                cv2.rectangle(image, (x, y), (x + w, y + h), self.COLOR_BOTON_BORDE, 2)
                self.draw_text(image, label, (x + 10, y + (h // 2) + 5), font_scale=0.5, color=self.COLOR_BOTON_TEXT)

            for label, (x, y, w, h) in self.scroll_buttons.items():
                cv2.rectangle(image, (x, y), (x + w, y + h), self.COLOR_BOTON_FONDO, -1)
                cv2.rectangle(image, (x, y), (x + w, y + h), self.COLOR_BOTON_BORDE, 2)
                self.draw_text(image, label, (x + 10, y + (h // 2) + 5), font_scale=0.4, color=self.COLOR_BOTON_TEXT)

    def draw_menu(self, image):
        if self.menu_visible:
            menu_height = 200
            cv2.rectangle(image, (0, image.shape[0] - menu_height), (image.shape[1], image.shape[0]), self.COLOR_MENU, -1)
            max_lines = 6  # Número de líneas visibles
            for i in range(max_lines):
                if self.scroll_offset + i < len(self.texts):
                    self.draw_text(image,
                                   self.texts[self.scroll_offset + i],
                                   (10, image.shape[0] - menu_height + 40 + i * 30),
                                   font_scale=0.5,
                                   color=self.COLOR_TEXTO_ABAJO)

            # Crear los botones de desplazamiento cuando el menú esté visible
            self.scroll_buttons = self.create_buttons({
                "up": "Up",
                "down": "Down"
            }, start_x=10, start_y=image.shape[0] - menu_height + 10, small=True)

    def draw_rectangles(self, image):
        for i, pos in enumerate(self.coordinate_generator.car_park_positions):
            center = (pos[0] + self.rect_widths[i] // 2, pos[1] + self.rect_heights[i] // 2)
            M = cv2.getRotationMatrix2D(center, self.rotation_angles[i], 1.0)
            rect = np.array([[pos[0], pos[1]], 
                             [pos[0] + self.rect_widths[i], pos[1]], 
                             [pos[0] + self.rect_widths[i], pos[1] + self.rect_heights[i]], 
                             [pos[0], pos[1] + self.rect_heights[i]]], dtype=np.float32)
            rotated_rect = cv2.transform(np.array([rect]), M)[0]

            color = self.COLOR_RECTANGULO
            if self.selected_rect == i:
                color = self.COLOR_RECTANGULO_SELECCIONADO
            cv2.polylines(image, [np.int32(rotated_rect)], isClosed=True, color=color, thickness=2)

            cv2.circle(image, (pos[0] + self.rect_widths[i], pos[1] + self.rect_heights[i]), 5, (0, 255, 0), -1)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            menu_x, menu_y, menu_w, menu_h = self.buttons["menu"]
            if menu_x <= x <= menu_x + menu_w and menu_y <= y <= menu_y + menu_h:
                self.menu_visible = not self.menu_visible
                return

            quit_x, quit_y, quit_w, quit_h = self.buttons["quit"]
            if quit_x <= x <= quit_x + quit_w and quit_y <= y <= quit_y + quit_h:
                self.cap.release()
                cv2.destroyAllWindows()
                exit()

            # Manejar botones de desplazamiento
            if self.menu_visible:
                scroll_up_x, scroll_up_y, scroll_up_w, scroll_up_h = self.scroll_buttons["up"]
                if scroll_up_x <= x <= scroll_up_x + scroll_up_w and scroll_up_y <= y <= scroll_up_y + scroll_up_h:
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                    return

                scroll_down_x, scroll_down_y, scroll_down_w, scroll_down_h = self.scroll_buttons["down"]
                if scroll_down_x <= x <= scroll_down_x + scroll_down_w and scroll_down_y <= y <= scroll_down_y + scroll_down_h:
                    self.scroll_offset = min(len(self.texts) - 1, self.scroll_offset + 1)
                    return

            if self.menu_visible:
                for label, (bx, by, bw, bh) in self.edit_buttons.items():
                    if bx <= x <= bx + bw and by <= y <= by + bh:
                        if label == "rotate":
                            self.rotate_selected_rectangle()
                        elif label == "delete":
                            self.delete_selected_rectangle()
                        elif label == "add":
                            self.add_rectangle()
                        elif label == "increase":
                            self.resize_selected_rectangle(10)
                        elif label == "decrease":
                            self.resize_selected_rectangle(-10)
                        elif label == "save":
                            self.save_positions()
                        return

            self.selected_rect = None
            for i, pos in enumerate(self.coordinate_generator.car_park_positions):
                if (pos[0] <= x <= pos[0] + self.rect_widths[i] and 
                        pos[1] <= y <= pos[1] + self.rect_heights[i]):
                    self.selected_rect = i
                    self.offset = (pos[0] - x, pos[1] - y)
                    self.dragging = True
                    return

                if (pos[0] + self.rect_widths[i] - 10 <= x <= pos[0] + self.rect_widths[i] + 10 and 
                        pos[1] + self.rect_heights[i] - 10 <= y <= pos[1] + self.rect_heights[i] + 10):
                    self.selected_rect = i
                    self.resizing = True
                    return

            if self.selected_rect is None:
                self.coordinate_generator.car_park_positions.append((x, y))
                self.rect_widths.append(self.coordinate_generator.rect_width)
                self.rect_heights.append(self.coordinate_generator.rect_height)
                self.rotation_angles.append(0)

            self.selected_rect = None

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging and self.selected_rect is not None:
                new_x = x + self.offset[0]
                new_y = y + self.offset[1]
                self.coordinate_generator.car_park_positions[self.selected_rect] = (new_x, new_y)

            if self.resizing and self.selected_rect is not None:
                new_width = x - self.coordinate_generator.car_park_positions[self.selected_rect][0]
                new_height = y - self.coordinate_generator.car_park_positions[self.selected_rect][1]
                self.rect_widths[self.selected_rect] = max(10, new_width)
                self.rect_heights[self.selected_rect] = max(10, new_height)

        elif event == cv2.EVENT_LBUTTONUP:
            if self.resizing:
                self.resizing = False
            else:
                self.dragging = False

        elif event == cv2.EVENT_RBUTTONDOWN:  # Manejo del clic derecho
            if self.selected_rect is None:  # Solo permite pegar si no hay selección
                self.camera_url += pyperclip.paste()  # Pegar texto del portapapeles

    def rotate_selected_rectangle(self):
        if self.selected_rect is not None:
            self.rotation_angles[self.selected_rect] += 3

    def delete_selected_rectangle(self):
        if self.selected_rect is not None:
            del self.coordinate_generator.car_park_positions[self.selected_rect]
            del self.rect_widths[self.selected_rect]
            del self.rect_heights[self.selected_rect]
            del self.rotation_angles[self.selected_rect]
            self.selected_rect = None

    def resize_selected_rectangle(self, delta):
        if self.selected_rect is not None:
            new_width = self.rect_widths[self.selected_rect] + delta
            new_height = self.rect_heights[self.selected_rect] + delta
            if new_width > 0 and new_height > 0:
                self.rect_widths[self.selected_rect] = new_width
                self.rect_heights[self.selected_rect] = new_height

    def add_rectangle(self):
        new_pos = (50, 50)
        self.coordinate_generator.car_park_positions.append(new_pos)
        self.rect_widths.append(self.coordinate_generator.rect_width)
        self.rect_heights.append(self.coordinate_generator.rect_height)
        self.rotation_angles.append(0)

    def save_positions(self):
        self.coordinate_generator.save_positions(
            [(pos[0], pos[1]) for pos in self.coordinate_generator.car_park_positions],
            self.rotation_angles,
            self.rect_widths,
            self.rect_heights
        )

    def open_url_input_window(self):
        url_window = np.zeros((200, 400, 3), dtype=np.uint8)
        cv2.namedWindow("Input URL", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Input URL", 400, 200)

        # Mostrar instrucciones
        cv2.putText(url_window, "Ingrese URL de la cámara:", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(url_window, self.camera_url, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        while True:
            cv2.imshow("Input URL", url_window)
            key = cv2.waitKey(1)

            if key == 27:  # Esc para salir de la ventana de entrada
                break

            # Verificar la validez de la URL al presionar Enter
            if key == 13:  # Enter
                self.cap.release()
                self.cap = cv2.VideoCapture(self.camera_url)
                cv2.destroyWindow("Input URL")  # Cerrar la ventana de entrada
                self.show_camera_status()  # Mostrar el estado de la cámara
                return  # Salir de la función

            elif key == 8:  # Backspace
                self.camera_url = self.camera_url[:-1]
            elif 32 <= key <= 126:  # Solo caracteres imprimibles
                self.camera_url += chr(key)

            # Actualizar la visualización de la URL
            url_window[:] = (0, 0, 0)  # Limpiar la ventana
            cv2.putText(url_window, "Ingrese URL de la cámara:", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(url_window, self.camera_url, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.destroyWindow("Input URL")

    def show_camera_status(self):
        status_window = np.zeros((200, 400, 3), dtype=np.uint8)
        cv2.namedWindow("Camera Status", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Camera Status", 400, 200)

        message = "Cámara conectada" if self.cap.isOpened() else "Cámara no encontrada"
        color = (0, 255, 0) if self.cap.isOpened() else (0, 0, 255)  # Verde o Rojo

        cv2.putText(status_window, message, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

        # Mostrar la ventana hasta que se cierre o se presione Esc
        while True:
            cv2.imshow("Camera Status", status_window)
            key = cv2.waitKey(1)

            if key == 27:  # Esc para cerrar la ventana
                break
            
            # Cerrar la ventana al hacer clic en la "X"
            if cv2.getWindowProperty("Camera Status", cv2.WND_PROP_VISIBLE) < 1:
                break

        # Verificar que la ventana esté abierta antes de intentar destruirla
        if cv2.getWindowProperty("Camera Status", cv2.WND_PROP_VISIBLE) >= 1:
            cv2.destroyWindow("Camera Status")

        # Restablecer a la cámara principal si no se pudo conectar
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(self.cameras[self.current_camera_index])

    def run(self):
        cv2.namedWindow("Camera", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Camera", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while True:
            ret, image = self.cap.read()
            if not ret:
                print("Error al leer el fotograma de la cámara.")
                break

            self.draw_rectangles(image)
            self.draw_menu(image)
            self.draw_buttons(image)

            cv2.imshow("Camera", image)
            cv2.setMouseCallback("Camera", self.mouse_callback)

            key = cv2.waitKey(1)
            if key == ord("c"):  # Cambiar cámara
                self.switch_camera()
            elif key == ord("r"):
                self.rotate_selected_rectangle()
            elif key == ord("d"):
                self.delete_selected_rectangle()
            elif key == ord("s"):
                self.save_positions()
            elif key == ord("a"):
                self.add_rectangle()
            elif key == ord("+"):
                self.resize_selected_rectangle(10)
            elif key == ord("-"):
                self.resize_selected_rectangle(-10)
            elif key == 13:  # Enter
                self.menu_visible = not self.menu_visible
            elif key == 9:  # Tab
                self.open_url_input_window()  # Abrir ventana para ingresar URL
            elif key == ord("q"):
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    manipulator = CoordinateManipulator()
    manipulator.run()