from flask import Flask, render_template
from predictest_7 import predecir_proximo_espacio_libre  # Importar la función de predicción

app = Flask(__name__)

@app.route("/")
def index():
    # Obtener la predicción del próximo espacio libre
    espacio_predicho = predecir_proximo_espacio_libre()
    return render_template("index.html", espacio_predicho=espacio_predicho)

if __name__ == "__main__":
    # Usa una de las opciones para evitar la ejecución doble
    app.run(debug=True, use_reloader=False)  # Opción más directa
