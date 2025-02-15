import os

def predict_next_free_space():
    # Crear un ejemplo de predicción
    prediccion = "Espacio 10 libre"
    
    file_path = "demo9.txt"  # Ruta al archivo

    try:
        # Verificar si el archivo existe
        if os.path.exists(file_path):
            print(f"El archivo '{file_path}' existe, se procederá a escribir.")
        else:
            print(f"El archivo '{file_path}' no existe, se creará.")
        
        # Intentamos escribir en el archivo
        with open(file_path, "w") as file:
            file.write(prediccion)
        
        # Confirmación de escritura
        print(f"Predicción guardada: {prediccion}")
        
    except Exception as e:
        # Si ocurre un error, imprimirlo
        print(f"Error al escribir en el archivo: {str(e)}")

# Llamar a la función para hacer una prueba
predict_next_free_space()
