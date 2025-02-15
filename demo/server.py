import mysql.connector 
import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import os

def predict_next_free_space():
    # Conexión a la base de datos MySQL
    db_config = {
        "host": "localhost",       # Cambiar por tu host
        "user": "root",            # Cambiar por tu usuario
        "password": "",           # Cambiar por tu contraseña
        "database": "car_parking" # Cambiar por tu base de datos
    }

    try:
        # Conectar a MySQL
        connection = mysql.connector.connect(**db_config)
        query = """
            SELECT parking_spaces_id, hora_llegada, hora_salida, TIMESTAMPDIFF(MINUTE, hora_llegada, hora_salida) as duracion
            FROM parking_records
            ORDER BY hora_llegada DESC
        """
        # Leer los datos desde la base de datos
        df = pd.read_sql(query, connection)

        # Convertir columnas de tiempo
        df["hora_llegada"] = pd.to_datetime(df["hora_llegada"])
        df["hora_salida"] = pd.to_datetime(df["hora_salida"])

        # Extraer características relevantes
        df["hora"] = df["hora_llegada"].dt.hour
        df["minuto"] = df["hora_llegada"].dt.minute
        df["dia"] = df["hora_llegada"].dt.day
        df["mes"] = df["hora_llegada"].dt.month

        # Seleccionar columnas de entrada y salida
        features = ["parking_spaces_id", "hora", "minuto", "dia", "mes", "duracion"]
        target = ["parking_spaces_id"]

        X = df[features].values
        y = df[target].values

        # Normalizar los datos
        scaler_X = MinMaxScaler()
        scaler_y = MinMaxScaler()
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y)

        # Reshape para LSTM
        X_scaled = np.reshape(X_scaled, (X_scaled.shape[0], 1, X_scaled.shape[1]))

        # Crear el modelo LSTM
        model = Sequential()
        model.add(LSTM(50, activation='relu', input_shape=(1, X_scaled.shape[2])))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mse')

        # Entrenar el modelo
        model.fit(X_scaled, y_scaled, epochs=50, batch_size=32, verbose=0)

        # Tomar los últimos datos para predecir
        ultimo_registro = X_scaled[-1].reshape(1, 1, X_scaled.shape[2])
        proxima_prediccion_scaled = model.predict(ultimo_registro)

        # Invertir la escala de la predicción
        proximo_espacio = scaler_y.inverse_transform(proxima_prediccion_scaled)[0][0]

        # Escribir el resultado en demo9.txt con codificación UTF-8
        with open("demo9.txt", "w", encoding="utf-8") as file:
            file.write(f"El proximo espacio libre:{int(proximo_espacio)}\n")
            file.write("Esta predicción se actualiza automáticamente.\n")

        print(f"Proximo libre: {int(proximo_espacio)}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if connection.is_connected():
            connection.close()

def read_prediction():
    try:
        with open("demo9.txt", "r", encoding="utf-8") as file:
            prediction = file.readlines()
            if prediction:
                print(f"Predicción leída: {prediction[0]}")
                return prediction[0].strip()
            else:
                print("No se ha encontrado predicción en el archivo.")
                return "No disponible"
    except Exception as e:
        print(f"Error al leer el archivo: {str(e)}")
        return "Error al leer la predicción"

# Llamada de ejemplo para probar la predicción
predict_next_free_space()
prediction = read_prediction()
print(f"Prediccion actual: {prediction}")
