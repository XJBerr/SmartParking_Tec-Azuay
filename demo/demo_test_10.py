import cv2
import numpy as np
import tkinter as tk
from src.utils_V9 import Park_classifier
from server import predict_next_free_space  # Importar la función de predicción

# Variable global para controlar el cierre de la aplicación
close_app = False
current_camera_index = 0  # Índice de la cámara actual
cameras = []  # Lista para almacenar las cámaras disponibles
prediction_text = "Predicción no disponible"  # Texto inicial de la predicción

def show_instructions():
    """Muestra la ventana de instrucciones."""
    instructions_window = tk.Toplevel()
    instructions_window.title("Instrucciones")
    instructions_window.geometry("300x150")
    
    instructions_message = (
        "Presiona 'q' para cerrar la cámara.\n"
        "Presiona 'c' para cambiar de cámara.\n"
        "Presiona 's' para hacer una captura."
    )
    
    label = tk.Label(instructions_window, text=instructions_message, padx=10, pady=10)
    label.pack()

    # Botón para ingresar al programa principal
    button = tk.Button(instructions_window, text="Aceptar e Ingresar al programa", command=instructions_window.destroy)
    button.pack(pady=10)

def mouse_callback(event, x, y, flags, param):
    global close_app, prediction_text
    # Verificar si se hizo clic izquierdo
    if event == cv2.EVENT_LBUTTONDOWN:
        # Verificar si se hizo clic en el área del botón 'Cerrar Cámara'
        if button_x <= x <= button_x + button_width and button_y <= y <= button_y + button_height:
            close_app = True
        # Verificar si se hizo clic en el botón 'Mostrar Predicción'
        if prediction_button_x <= x <= prediction_button_x + prediction_button_width and \
           prediction_button_y <= y <= prediction_button_y + prediction_button_height:
            # Llamar a la función de predicción y actualizar el texto
            try:
                predict_next_free_space()  # Actualizar demo9.txt con la predicción
                with open("demo9.txt", "r", encoding="utf-8") as file:
                    prediction_text = file.readline().strip()
            except Exception as e:
                prediction_text = f"Error: {str(e)}"

def get_available_cameras():
    """Obtiene una lista de cámaras disponibles."""
    available_cameras = []
    for i in range(2):  # Probar hasta 10 cámaras
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def demostration():
    """Demostración de la aplicación."""
    global button_x, button_y, button_width, button_height
    global prediction_button_x, prediction_button_y, prediction_button_width, prediction_button_height
    global current_camera_index, cameras, prediction_text

    # Definir el nombre de la ventana
    window_name = "Car Park Image"

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
    show_instructions()  # Mostrar la ventana de instrucciones

    # Coordenadas iniciales para los botones
    button_x, button_y = 500, 30  # 'Cerrar Cámara' en la parte superior derecha
    prediction_button_x, prediction_button_y = 20, 400  # 'Mostrar Predicción' en la parte inferior izquierda

    # Configurar la ventana OpenCV para pantalla completa
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

            # Dibujar el botón 'Mostrar Predicción'
            text_size_button = cv2.getTextSize("Mostrar Prediccion", cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            prediction_button_width, prediction_button_height = text_size_button[0] + 20, text_size_button[1] + 20
            cv2.rectangle(denoted_image, (prediction_button_x, prediction_button_y), 
                          (prediction_button_x + prediction_button_width, prediction_button_y + prediction_button_height), (0, 255, 0), -1)
            cv2.putText(denoted_image, "Mostrar Prediccion", 
                        (prediction_button_x + 10, prediction_button_y + text_size_button[1] + 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

            # Dibujar el cuadro de texto dinámico para la predicción
            text_size_pred = cv2.getTextSize(f"Pred {prediction_text}", cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            pred_box_x = prediction_button_x
            pred_box_y = prediction_button_y + prediction_button_height + 10
            cv2.rectangle(denoted_image, 
                          (pred_box_x, pred_box_y), 
                          (pred_box_x + text_size_pred[0] + 10, pred_box_y + text_size_pred[1] + 10), (0, 0, 255), -1)
            cv2.putText(denoted_image, f">{prediction_text}", 
                        (pred_box_x + 5, pred_box_y + text_size_pred[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

            # Dibujar el botón 'Cerrar Cámara'
            text_size_close = cv2.getTextSize("Cerrar Camara", cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            button_width, button_height = text_size_close[0] + 20, text_size_close[1] + 20
            cv2.rectangle(denoted_image, (button_x, button_y), (button_x + button_width, button_y + button_height), (200, 0, 190), -1)
            cv2.putText(denoted_image, "Cerrar Camara", 
                        (button_x + 10, button_y + text_size_close[1] + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

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

    finally:
        # Asegurarse de guardar registros de salida pendientes al cerrar
        print("Guardando registros de salida antes de cerrar...")
        classifier.handle_exit()
        cap.release()
        cv2.destroyAllWindows()
        classifier.db_manager.close_connection()  # Cerrar la conexión a la base de datos

if __name__ == "__main__":
    demostration()
