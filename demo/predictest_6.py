import pymysql
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score
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

    # Crear variables adicionales
    df['hora_ocupado'] = df['hora_llegada'].dt.hour  # Hora del día
    df['dia_semana'] = df['hora_llegada'].dt.weekday  # Día de la semana

    # 🔹 Seleccionar las características de entrada (X) y la variable de salida (y)
    X = df[['hora_ocupado', 'duracion', 'dia_semana']]  # Incluyendo día de la semana
    y = df['parking_spaces_id']

    # 🔹 Normalizar los datos
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Dividir en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # 🔹 Crear la red neuronal
    model = Sequential([
        Dense(10, activation='relu', input_shape=(X_train.shape[1],)),  # 3 entradas: hora ocupación, duración, día semana
        Dense(10, activation='relu'),
        Dense(1, activation='linear')  # Salida: Predicción del espacio libre
    ])

    # 🔹 Compilar el modelo
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])

    # 🔹 Entrenar la red neuronal
    model.fit(X_train, y_train, epochs=100, verbose=1)

    # 🔹 Evaluar el modelo
    loss, mae = model.evaluate(X_test, y_test, verbose=0)
    print(f"🔹 Evaluación del modelo: Loss (MSE)={loss:.2f}, MAE={mae:.2f}")

    # Métrica personalizada: Precisión del modelo
    y_pred = model.predict(X_test)
    y_pred = np.round(y_pred).astype(int)  # Redondear predicciones al espacio más cercano
    precision = accuracy_score(y_test, y_pred)
    print(f"🔹 Precisión del modelo: {precision * 100:.2f}%")

    # 🔹 Función para predecir el próximo espacio libre
    def predecir_proximo_espacio_libre():
        """
        Usa la red neuronal para predecir qué espacio será el próximo en liberarse.
        """
        hora_actual = datetime.datetime.now().hour
        dia_actual = datetime.datetime.now().weekday()
        # Estimamos un tiempo de ocupación promedio basado en el dataset
        tiempo_promedio = df['duracion'].mean()
        
        # Crear entrada para la predicción
        entrada = np.array([[hora_actual, tiempo_promedio, dia_actual]])
        entrada_scaled = scaler.transform(entrada)

        # Hacer la predicción
        prediccion = model.predict(entrada_scaled)
        espacio_predicho = int(prediccion[0][0])

        print(f"🔮 Predicción con Red Neuronal: El próximo espacio en liberarse será el espacio {espacio_predicho}.")
        return espacio_predicho

    # 🔄 Llamar a la función para predecir el espacio libre
    espacio_predicho = predecir_proximo_espacio_libre()

    # 🔹 Validar la predicción con la base de datos
    def validar_prediccion(espacio_predicho):
        """
        Valida la predicción consultando la base de datos.
        """
        try:
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()

            query = f"""
            SELECT parking_spaces_id, hora_salida 
            FROM parking_records 
            WHERE parking_spaces_id = {espacio_predicho} 
            ORDER BY hora_salida DESC 
            LIMIT 1;
            """
            cursor.execute(query)
            resultado = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if resultado:
                print(f"📊 Validación: El espacio {resultado[0]} tiene hora_salida: {resultado[1]}")
            else:
                print("⚠️ No se encontraron datos para validar la predicción.")
        except Exception as e:
            print(f"Error al validar la predicción: {e}")

    validar_prediccion(espacio_predicho)
