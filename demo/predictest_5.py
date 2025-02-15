import pymysql
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.preprocessing import MinMaxScaler
import datetime

# 🔹 Configurar la conexión a MySQL
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "car_parking"
}

def obtener_historial_espacios():
    """
    Obtiene el historial de ocupación y liberación de los espacios desde MySQL.
    """
    try:
        # Conectar a la base de datos
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # Consulta SQL para obtener los datos
        query = """
        SELECT parking_spaces_id, hora_llegada, hora_salida
        FROM parking_records
        WHERE hora_llegada IS NOT NULL AND hora_salida IS NOT NULL
        ORDER BY hora_llegada DESC
        """
        
        cursor.execute(query)
        datos = cursor.fetchall()

        # Convertir a DataFrame
        df = pd.DataFrame(datos, columns=['parking_spaces_id', 'hora_llegada', 'hora_salida'])

        # Cerrar conexión
        cursor.close()
        conn.close()

        return df

    except Exception as e:
        print(f"Error al obtener datos de MySQL: {e}")
        return pd.DataFrame()  # Retornar un DataFrame vacío si hay error

# 🔹 Obtener los datos
df = obtener_historial_espacios()

if df.empty:
    print("⚠️ No se encontraron datos en la tabla parking_records. Verifica la base de datos.")
else:
    # Convertir a datetime
    df['hora_llegada'] = pd.to_datetime(df['hora_llegada'])
    df['hora_salida'] = pd.to_datetime(df['hora_salida'])

    # Calcular la duración de ocupación en segundos
    df['duracion'] = (df['hora_salida'] - df['hora_llegada']).dt.total_seconds()

    # Crear una variable de hora del día (para aprender patrones de uso)
    df['hora_ocupado'] = df['hora_llegada'].dt.hour

    # 🔹 Seleccionar las características de entrada (X) y la variable de salida (y)
    X = df[['hora_ocupado', 'duracion']]
    y = df['parking_spaces_id']

    # 🔹 Normalizar los datos
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # 🔹 Crear la red neuronal
    model = Sequential([
        Dense(10, activation='relu', input_shape=(2,)),  # 2 entradas: hora ocupación y duración
        Dense(10, activation='relu'),
        Dense(1, activation='linear')  # Salida: Predicción del espacio libre
    ])

    # 🔹 Compilar el modelo
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    # 🔹 Entrenar la red neuronal
    model.fit(X_scaled, y, epochs=100, verbose=1)

    # 🔹 Función para predecir el próximo espacio libre
    def predecir_proximo_espacio_libre():
        """
        Usa la red neuronal para predecir qué espacio será el próximo en liberarse.
        """
        hora_actual = datetime.datetime.now().hour
        # Estimamos un tiempo de ocupación promedio basado en el dataset
        tiempo_promedio = df['duracion'].mean()
        
        # Crear entrada para la predicción
        entrada = np.array([[hora_actual, tiempo_promedio]])
        entrada_scaled = scaler.transform(entrada)

        # Hacer la predicción
        prediccion = model.predict(entrada_scaled)
        espacio_predicho = int(prediccion[0][0])

        print(f"🔮 Predicción con Red Neuronal: El próximo espacio en liberarse será el espacio {espacio_predicho}.")
        return espacio_predicho

    # 🔄 Llamar a la función para predecir el espacio libre
    espacio_predicho = predecir_proximo_espacio_libre()
