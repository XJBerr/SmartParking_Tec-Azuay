import cv2
import numpy as np
from src.utils_V9 import Park_classifier  # Asegúrate de usar utils_v3 actualizado

# Variables globales
close_app = False
current_camera_index = 0  # Índice de la cámara actual
cameras = []  # Lista para almacenar las cámaras disponibles
camera_url = ""  # Variable para almacenar la URL de la cámara
menu_visible = False  # Controla la visibilidad del menú
scroll_offset = 0  # Controla el desplazamiento del menú

# Colores
COLOR_MENU = (220, 220, 220)  # Color de fondo del menú
COLOR_BOTON_FONDO = (200, 0, 190)  # Color de fondo de los botones (igual que "Close Camera")
COLOR_BOTON_TEXT = (255, 255, 255)  # Color del texto de los botones (blanco)
COLOR_BOTON_BORDE = (0, 0, 0)  # Color del borde de los botones

# Textos del menú
texts = ["",
    "Instrucciones de uso:",
    "- Presiona 'q' para cerrar la camara",
    "- Presiona 'c' para cambiar de camara",
    "- Presiona 's' para hacer una captura",
    "- Presiona 'Tab' para ingresar una URL de camara",
    "- Presiona 'Enter' para conectar a la camara",
    "- Presiona 'Esc' para salir del menu de la camara por url"
]

def mouse_callback(event, x, y, flags, param):
    global close_app, menu_visible, scroll_offset

    # Verificar si se hizo clic izquierdo
    if event == cv2.EVENT_LBUTTONDOWN:
        # Verificar si se hizo clic en el área del botón "Close Camera"
        if button_x <= x <= button_x + button_width and button_y <= y <= button_y + button_height:
            close_app = True

        # Verificar si se hizo clic en el área del botón "Inst"
        if inst_button_x <= x <= inst_button_x + inst_button_width and inst_button_y <= y <= inst_button_y + inst_button_height:
            menu_visible = not menu_visible  # Alternar visibilidad del menú

        # Verificar si se hizo clic en los botones de desplazamiento del menú
        if menu_visible:
            if scroll_up_x <= x <= scroll_up_x + scroll_up_width and scroll_up_y <= y <= scroll_up_y + scroll_up_height:
                scroll_offset = max(0, scroll_offset - 1)  # Desplazar hacia arriba
            if scroll_down_x <= x <= scroll_down_x + scroll_down_width and scroll_down_y <= y <= scroll_down_y + scroll_down_height:
                scroll_offset = min(len(texts) - 1, scroll_offset + 1)  # Desplazar hacia abajo

def draw_menu(image):
    """Dibuja el menú desplegable en la parte inferior de la imagen."""
    global menu_visible, scroll_offset

    if menu_visible:
        menu_height = 200  # Altura del menú
        # Dibujar el fondo del menú con un borde
        cv2.rectangle(image, (0, image.shape[0] - menu_height), (image.shape[1], image.shape[0]), COLOR_MENU, -1)
        cv2.rectangle(image, (0, image.shape[0] - menu_height), (image.shape[1], image.shape[0]), (0, 0, 0), 2)

        # Dibujar las instrucciones
        max_lines = 6  # Número de líneas visibles
        for i in range(max_lines):
            if scroll_offset + i < len(texts):
                cv2.putText(image, texts[scroll_offset + i], (20, image.shape[0] - menu_height + 40 + i * 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        # Dibujar los botones de desplazamiento
        global scroll_up_x, scroll_up_y, scroll_up_width, scroll_up_height
        global scroll_down_x, scroll_down_y, scroll_down_width, scroll_down_height

        scroll_up_x, scroll_up_y, scroll_up_width, scroll_up_height = 10, image.shape[0] - menu_height + 10, 50, 20
        scroll_down_x, scroll_down_y, scroll_down_width, scroll_down_height = 70, image.shape[0] - menu_height + 10, 50, 20

        cv2.rectangle(image, (scroll_up_x, scroll_up_y), (scroll_up_x + scroll_up_width, scroll_up_y + scroll_up_height), COLOR_BOTON_FONDO, -1)
        cv2.putText(image, "Up", (scroll_up_x + 10, scroll_up_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_BOTON_TEXT, 1)

        cv2.rectangle(image, (scroll_down_x, scroll_down_y), (scroll_down_x + scroll_down_width, scroll_down_y + scroll_down_height), COLOR_BOTON_FONDO, -1)
        cv2.putText(image, "Down", (scroll_down_x + 10, scroll_down_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_BOTON_TEXT, 1)

def get_available_cameras():
    """Obtiene una lista de cámaras disponibles."""
    available_cameras = []
    for i in range(2):  # Probar hasta 10 cámaras
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def open_url_input_window():
    """Abre una ventana para que el usuario ingrese la URL de la cámara."""
    global camera_url

    url_window = np.zeros((200, 400, 3), dtype=np.uint8)
    cv2.namedWindow("Input URL", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Input URL", 400, 200)

    # Mostrar instrucciones
    cv2.putText(url_window, "Ingrese URL de la camara:", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(url_window, camera_url, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    while True:
        cv2.imshow("Input URL", url_window)
        key = cv2.waitKey(1)

        if key == 27:  # Esc para salir de la ventana de entrada
            break

        # Verificar la validez de la URL al presionar Enter
        if key == 13:  # Enter
            cv2.destroyWindow("Input URL")  # Cerrar la ventana de entrada
            show_camera_status()  # Mostrar el estado de la cámara
            return  # Salir de la función

        elif key == 8:  # Backspace
            camera_url = camera_url[:-1]
        elif 32 <= key <= 126:  # Solo caracteres imprimibles
            camera_url += chr(key)

        # Actualizar la visualización de la URL
        url_window[:] = (0, 0, 0)  # Limpiar la ventana
        cv2.putText(url_window, "Ingrese URL de la camara:", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(url_window, camera_url, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    cv2.destroyWindow("Input URL")

def show_camera_status():
    """Muestra el estado de la cámara después de intentar conectarse."""
    global cap, camera_url

    status_window = np.zeros((200, 400, 3), dtype=np.uint8)
    cv2.namedWindow("Camera Status", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Camera Status", 400, 200)

    # Intentar abrir la cámara con la URL ingresada
    new_cap = cv2.VideoCapture(camera_url)
    if new_cap.isOpened():
        cap.release()  # Liberar la cámara actual
        cap = new_cap  # Asignar la nueva cámara
        message = "Camara conectada"
        color = (0, 255, 0)  # Verde
    else:
        message = "Camara no encontrada"
        color = (0, 0, 255)  # Rojo

    cv2.putText(status_window, message, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

    # Mostrar la ventana hasta que se cierre o se presione Esc
    while True:
        cv2.imshow("Camera Status", status_window)
        key = cv2.waitKey(1)

        if key == 27:  # Esc para cerrar la ventana
            break

    cv2.destroyWindow("Camera Status")

def demostration():
    """Demostración de la aplicación."""
    global button_x, button_y, button_width, button_height, current_camera_index, cameras, cap, camera_url
    global inst_button_x, inst_button_y, inst_button_width, inst_button_height

    # Definición de los parámetros
    positions_json_path = "positions.json"  # Ruta al archivo JSON
    rect_width, rect_height = 50, 30  # Tamaños predeterminados de los cuadros

    # Creando la instancia del clasificador
    classifier = Park_classifier(positions_json_path, rect_width, rect_height)

    # Obtener las cámaras disponibles
    cameras = get_available_cameras()
    if not cameras:
        print("No se encontraron cámaras disponibles.")
        return

    # Inicializa la captura de video desde la cámara actual
    cap = cv2.VideoCapture(cameras[current_camera_index])

    # Definir las coordenadas y tamaño del botón "Close Camera"
    button_x, button_y, button_width, button_height = 500, 30, 120, 40

    # Definir las coordenadas y tamaño del botón "Inst" (a la izquierda de "Close Camera")
    inst_button_x, inst_button_y, inst_button_width, inst_button_height = button_x - 130, button_y, 80, 40

    # Establecer el callback del mouse
    window_name = "Car Park Image"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    try:
        while True:
            # Leyendo el video frame por frame
            ret, frame = cap.read()

            # Verificando si se ha capturado un frame válido
            if not ret:
                break
            
            # Procesando los frames para preparar la clasificación
            processed_frame = classifier.implement_process(frame)
            
            # Dibujando los espacios de estacionamiento de acuerdo a su estado 
            denoted_image = classifier.classify(image=frame, processed_image=processed_frame)

            # Dibujar el botón 'Close Camera'
            cv2.rectangle(denoted_image, (button_x, button_y), (button_x + button_width, button_y + button_height), COLOR_BOTON_FONDO, -1)
            cv2.putText(denoted_image, 'Close Camera', (button_x + 5, button_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_BOTON_TEXT, 1)

            # Dibujar el botón 'Inst'
            cv2.rectangle(denoted_image, (inst_button_x, inst_button_y), (inst_button_x + inst_button_width, inst_button_y + inst_button_height), COLOR_BOTON_FONDO, -1)
            cv2.putText(denoted_image, 'Instruct', (inst_button_x + 10, inst_button_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_BOTON_TEXT, 1)

            # Dibujar el menú desplegable
            draw_menu(denoted_image)

            # Mostrando los resultados
            cv2.imshow(window_name, denoted_image)

            # Captura de la tecla presionada
            k = cv2.waitKey(1)

            # Condición de salida
            if k & 0xFF == ord('q') or close_app:  # Presiona 'q' o clic en el botón para cerrar
                print("Saliendo del programa...")
                classifier.handle_exit()  # Guardar las salidas antes de cerrar
                cv2.waitKey(1000)  # Esperar un segundo antes de cerrar
                break

            if k & 0xFF == ord('s'):  # Presiona 's' para guardar la imagen
                cv2.imwrite("output.jpg", denoted_image)

            if k & 0xFF == ord('c'):  # Presiona 'c' para cambiar de cámara
                cap.release()  # Liberar la cámara actual
                current_camera_index = (current_camera_index + 1) % len(cameras)  # Cambiar al siguiente índice
                cap = cv2.VideoCapture(cameras[current_camera_index])  # Abrir la nueva cámara
                print(f"Cámara cambiada a: {cameras[current_camera_index]}")

            if k & 0xFF == 9:  # Presiona 'Tab' para ingresar una URL de cámara
                open_url_input_window()  # Abrir ventana para ingresar URL

    finally:
        # Asegurarse de guardar registros de salida pendientes al cerrar
        print("Guardando registros de salida antes de cerrar...")
        classifier.handle_exit()
        cap.release()
        cv2.destroyAllWindows()
        classifier.db_manager.close_connection()  # Cerrar la conexión a la base de datos

if __name__ == "__main__":
    demostration()