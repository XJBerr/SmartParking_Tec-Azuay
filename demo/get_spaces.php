<?php 
header('Content-Type: application/json');

// Conexión a la base de datos
$host = "localhost";
$user = "root"; // Usuario de MySQL
$password = ""; // Contraseña de MySQL
$database = "car_parking"; // Nombre de tu base de datos

$conn = new mysqli($host, $user, $password, $database);

// Verificar conexión
if ($conn->connect_error) {
    die(json_encode(['error' => 'Conexión fallida: ' . $conn->connect_error]));
}

// Consulta SQL mejorada para obtener los espacios y sus estados
$sql = "
SELECT 
    sd.parking_spaces_id_sd,
    sd.estado,
    sd.hora_cambio,
    CASE
        WHEN sd.estado = 'Libre' THEN 'Hora desde que se desocupó'
        WHEN sd.estado = 'Ocupado' THEN 'Hora desde que se ocupó'
        ELSE 'Estado desconocido'
    END AS descripcion_estado
FROM state_date sd
INNER JOIN (
    SELECT 
        parking_spaces_id_sd, 
        MAX(hora_cambio) AS max_hora_cambio
    FROM state_date
    WHERE fecha = DATE(NOW())
    GROUP BY parking_spaces_id_sd
) latest
ON sd.parking_spaces_id_sd = latest.parking_spaces_id_sd
AND sd.hora_cambio = latest.max_hora_cambio;
";

$result = $conn->query($sql);

// Preparar los datos
$spaces = [];
$libres = 0;
$ocupados = 0;

if ($result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $spaces[] = $row;

        // Incrementar contadores según el estado
        if ($row['estado'] === "Libre") {
            $libres++;
        } else {
            $ocupados++;
        }
    }
}

// Leer predicción desde el archivo
$prediccion_file = "prediccion.txt";
$prediccion = null;

if (file_exists($prediccion_file)) {
    $prediccion = trim(file_get_contents($prediccion_file));
} else {
    $prediccion = "Sin datos de predicción";
}

// Respuesta en formato JSON
echo json_encode([
    'spaces' => $spaces,
    'libres' => $libres,
    'ocupados' => $ocupados,
    'total' => $libres + $ocupados,
    'prediccion' => $prediccion
]);

$conn->close();
?>
