import os
import re
import secrets
from datetime import date
from functools import wraps

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

viajes = [
    {
        "id": "paris",
        "country": "Francia",
        "city": "París",
        "description": "Arte, cafés y paseos junto al Sena.",
        "price": 850,
        "days": 5,
        "emoji": "🇫🇷",
    },
    {
        "id": "tokyo",
        "country": "Japón",
        "city": "Tokio",
        "description": "Tradición y tecnología en una ciudad inolvidable.",
        "price": 1450,
        "days": 7,
        "emoji": "🇯🇵",
    },
    {
        "id": "barcelona",
        "country": "España",
        "city": "Barcelona",
        "description": "Arquitectura, playa y sabores mediterráneos.",
        "price": 720,
        "days": 5,
        "emoji": "🇪🇸",
    },
    {
        "id": "new-york",
        "country": "Estados Unidos",
        "city": "Nueva York",
        "description": "Una escapada entre rascacielos, museos y parques.",
        "price": 1200,
        "days": 6,
        "emoji": "🇺🇸",
    },
    {
        "id": "rio",
        "country": "Brasil",
        "city": "Río de Janeiro",
        "description": "Playas, música y paisajes tropicales.",
        "price": 680,
        "days": 5,
        "emoji": "🇧🇷",
    },
    {
        "id": "cusco",
        "country": "Perú",
        "city": "Cusco",
        "description": "Historia andina y aventura hacia Machu Picchu.",
        "price": 590,
        "days": 4,
        "emoji": "🇵🇪",
    },
]


def conectar_a_mysql():
    """Abre una conexión a la base de datos del proyecto."""
    password = os.getenv("MYSQL_PASSWORD")
    if password is None:
        raise RuntimeError("Agrega MYSQL_PASSWORD al archivo .env.")

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=password,
        database=os.getenv("MYSQL_DATABASE", "viajes_app"),
        charset="utf8mb4",
    )


def crear_base_y_tabla():
    """Crea las tablas necesarias y agrega user_id a instalaciones anteriores."""
    nombre_base = os.getenv("MYSQL_DATABASE", "viajes_app")
    if re.fullmatch(r"[A-Za-z0-9_]+", nombre_base) is None:
        raise RuntimeError("El nombre de MYSQL_DATABASE no es válido.")

    password = os.getenv("MYSQL_PASSWORD")
    if password is None:
        raise RuntimeError("Agrega MYSQL_PASSWORD al archivo .env.")

    conexion = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=password,
        charset="utf8mb4",
    )
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS `" + nombre_base + "` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    finally:
        conexion.close()

    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                email VARCHAR(254) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT UNSIGNED NULL,
                customer_name VARCHAR(120) NOT NULL,
                customer_email VARCHAR(254) NOT NULL,
                trip_id VARCHAR(40) NOT NULL,
                departure_date DATE NOT NULL,
                travelers SMALLINT UNSIGNED NOT NULL,
                total_price DECIMAL(10, 2) NOT NULL,
                status ENUM('pending', 'confirmed') NOT NULL DEFAULT 'pending',
                ticket_code VARCHAR(24) UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_reservations_created_at (created_at),
                INDEX idx_reservations_user_id (user_id),
                CONSTRAINT fk_reservations_user
                    FOREIGN KEY (user_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.execute("SHOW COLUMNS FROM reservations LIKE 'user_id'")
        if cursor.fetchone() is None:
            cursor.execute(
                """
                ALTER TABLE reservations
                ADD COLUMN user_id BIGINT UNSIGNED NULL,
                ADD INDEX idx_reservations_user_id (user_id),
                ADD CONSTRAINT fk_reservations_user
                    FOREIGN KEY (user_id) REFERENCES users(id)
                """
            )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                reservation_id BIGINT UNSIGNED NOT NULL UNIQUE,
                method ENUM('card', 'pse') NOT NULL,
                status ENUM('demo_approved') NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_payments_reservation
                    FOREIGN KEY (reservation_id) REFERENCES reservations(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        conexion.commit()
    finally:
        conexion.close()


def buscar_viaje(id_viaje):
    for viaje in viajes:
        if viaje["id"] == id_viaje:
            return viaje
    return None


def validar_datos_reserva(datos):
    viaje = buscar_viaje(str(datos.get("trip_id", "")))
    nombre = str(datos.get("customer_name", "")).strip()
    correo = str(datos.get("customer_email", "")).strip()
    fecha = str(datos.get("departure_date", "")).strip()

    if viaje is None:
        raise ValueError("Selecciona uno de los destinos disponibles.")
    if not nombre or len(nombre) > 120:
        raise ValueError("Ingresa un nombre de hasta 120 caracteres.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo) or len(correo) > 254:
        raise ValueError("Ingresa un correo electrónico válido.")
    try:
        fecha_salida = date.fromisoformat(fecha)
    except ValueError as error:
        raise ValueError("Selecciona una fecha de salida válida.") from error
    if fecha_salida < date.today():
        raise ValueError("La fecha de salida no puede estar en el pasado.")
    try:
        cantidad_viajeros = int(datos.get("travelers", 0))
    except (ValueError, TypeError) as error:
        raise ValueError("La cantidad de viajeros debe ser de 1 a 9.") from error
    if cantidad_viajeros < 1 or cantidad_viajeros > 9:
        raise ValueError("La cantidad de viajeros debe ser de 1 a 9.")

    return {
        "trip": viaje,
        "name": nombre,
        "email": correo,
        "date": fecha_salida,
        "travelers": cantidad_viajeros,
        "total": viaje["price"] * cantidad_viajeros,
    }


def preparar_reserva(fila):
    viaje = buscar_viaje(fila[3])
    return {
        "id": fila[0],
        "customer_name": fila[1],
        "customer_email": fila[2],
        "trip_id": fila[3],
        "city": viaje["city"] if viaje else fila[3],
        "country": viaje["country"] if viaje else "",
        "departure_date": fila[4].isoformat(),
        "travelers": fila[5],
        "total_price": float(fila[6]),
        "status": fila[7],
        "ticket_code": fila[8],
        "payment_method": fila[9] if len(fila) > 9 else None,
        "payment_status": fila[10] if len(fila) > 10 else None,
    }


def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(error="Inicia sesión para continuar."), 401
        return view(*args, **kwargs)

    return wrapped


def obtener_datos_json():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


def nombre_usuario(user_id):
    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        fila = cursor.fetchone()
        if fila is None:
            session.clear()
            return None
        return {"id": fila[0], "name": fila[1], "email": fila[2]}
    finally:
        conexion.close()


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/api/trips")
def mostrar_viajes():
    return jsonify(viajes)


@app.route("/api/register", methods=["POST"])
def registrar_usuario():
    datos = obtener_datos_json()
    nombre = str(datos.get("name", "")).strip()
    correo = str(datos.get("email", "")).strip().lower()
    password = datos.get("password", "")

    if not nombre or len(nombre) > 120:
        return jsonify(error="Ingresa tu nombre (máximo 120 caracteres)."), 400
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo) or len(correo) > 254:
        return jsonify(error="Ingresa un correo electrónico válido."), 400
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        return jsonify(error="La contraseña debe tener entre 8 y 128 caracteres."), 400

    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (nombre, correo, generate_password_hash(password)),
        )
        conexion.commit()
        session.clear()
        session["user_id"] = cursor.lastrowid
        return jsonify(user={"id": cursor.lastrowid, "name": nombre, "email": correo}), 201
    except Error as error:
        conexion.rollback()
        if error.errno == 1062:
            return jsonify(error="Ya existe una cuenta con ese correo."), 409
        raise
    finally:
        conexion.close()


@app.route("/api/login", methods=["POST"])
def iniciar_sesion():
    datos = obtener_datos_json()
    correo = str(datos.get("email", "")).strip().lower()
    password = datos.get("password", "")
    if not correo or not isinstance(password, str):
        return jsonify(error="Ingresa tu correo y contraseña."), 400

    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = %s",
            (correo,),
        )
        fila = cursor.fetchone()
        if fila is None or not check_password_hash(fila[3], password):
            return jsonify(error="El correo o la contraseña no son correctos."), 401
        session.clear()
        session["user_id"] = fila[0]
        return jsonify(user={"id": fila[0], "name": fila[1], "email": fila[2]})
    finally:
        conexion.close()


@app.route("/api/logout", methods=["POST"])
def cerrar_sesion():
    session.clear()
    return jsonify(message="Sesión cerrada.")


@app.route("/api/me")
@require_login
def usuario_actual():
    user = nombre_usuario(session["user_id"])
    if user is None:
        return jsonify(error="Inicia sesión para continuar."), 401
    return jsonify(user=user)


@app.route("/api/reservations")
@require_login
def mostrar_reservas():
    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT r.id, r.customer_name, r.customer_email, r.trip_id,
                   r.departure_date, r.travelers, r.total_price, r.status,
                   r.ticket_code, p.method, p.status
            FROM reservations r
            LEFT JOIN payments p ON p.reservation_id = r.id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
            """,
            (session["user_id"],),
        )
        return jsonify([preparar_reserva(fila) for fila in cursor.fetchall()])
    finally:
        conexion.close()


@app.route("/api/reservations", methods=["POST"])
@require_login
def guardar_reserva():
    try:
        datos = validar_datos_reserva(obtener_datos_json())
    except ValueError as error:
        return jsonify(error=str(error)), 400

    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO reservations
                (user_id, customer_name, customer_email, trip_id,
                 departure_date, travelers, total_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                datos["name"],
                datos["email"],
                datos["trip"]["id"],
                datos["date"],
                datos["travelers"],
                datos["total"],
            ),
        )
        conexion.commit()
        return jsonify(
            id=cursor.lastrowid,
            status="pending",
            total_price=datos["total"],
            message="Reserva guardada en la base de datos.",
        ), 201
    finally:
        conexion.close()


@app.route("/api/reservations/<int:id_reserva>", methods=["PUT"])
@require_login
def editar_reserva(id_reserva):
    try:
        datos = validar_datos_reserva(obtener_datos_json())
    except ValueError as error:
        return jsonify(error=str(error)), 400

    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE reservations
            SET customer_name = %s, customer_email = %s, trip_id = %s,
                departure_date = %s, travelers = %s, total_price = %s
            WHERE id = %s AND user_id = %s AND status = 'pending'
            """,
            (
                datos["name"],
                datos["email"],
                datos["trip"]["id"],
                datos["date"],
                datos["travelers"],
                datos["total"],
                id_reserva,
                session["user_id"],
            ),
        )
        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT status FROM reservations WHERE id = %s AND user_id = %s",
                (id_reserva, session["user_id"]),
            )
            reserva = cursor.fetchone()
            if reserva is None:
                return jsonify(error="No se encontró la reserva."), 404
            return jsonify(error="Solo puedes editar reservas pendientes."), 409
        conexion.commit()
        return jsonify(message="Reserva actualizada.", total_price=datos["total"])
    finally:
        conexion.close()


@app.route("/api/reservations/<int:id_reserva>/payments", methods=["POST"])
@require_login
def simular_pago(id_reserva):
    metodo = obtener_datos_json().get("method")
    if metodo not in ("card", "pse"):
        return jsonify(error="Selecciona tarjeta o PSE para la simulación."), 400

    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT id, customer_name, customer_email, trip_id, departure_date,
                   travelers, total_price, status, ticket_code
            FROM reservations
            WHERE id = %s AND user_id = %s
            FOR UPDATE
            """,
            (id_reserva, session["user_id"]),
        )
        fila = cursor.fetchone()
        if fila is None:
            conexion.rollback()
            return jsonify(error="No se encontró la reserva."), 404

        cursor.execute(
            "SELECT method, status FROM payments WHERE reservation_id = %s",
            (id_reserva,),
        )
        pago = cursor.fetchone()
        if pago is None:
            cursor.execute(
                """
                INSERT INTO payments (reservation_id, method, status, amount)
                VALUES (%s, %s, 'demo_approved', %s)
                """,
                (id_reserva, metodo, fila[6]),
            )
        codigo_ticket = fila[8]
        if fila[7] == "pending":
            codigo_ticket = secrets.token_hex(6).upper()
            cursor.execute(
                """
                UPDATE reservations
                SET status = 'confirmed', ticket_code = %s
                WHERE id = %s AND user_id = %s
                """,
                (codigo_ticket, id_reserva, session["user_id"]),
            )
        conexion.commit()

        fila_actualizada = list(fila)
        fila_actualizada[7] = "confirmed"
        fila_actualizada[8] = codigo_ticket
        reserva = preparar_reserva(fila_actualizada)
        reserva["payment_method"] = pago[0] if pago else metodo
        reserva["payment_status"] = pago[1] if pago else "demo_approved"
        return jsonify(
            reservation=reserva,
            message="Simulación aprobada; no se realizó ningún cobro real.",
            demo=True,
        )
    finally:
        conexion.close()


@app.route("/api/reservations/<int:id_reserva>", methods=["DELETE"])
@require_login
def eliminar_reserva(id_reserva):
    conexion = conectar_a_mysql()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "DELETE FROM reservations WHERE id = %s AND user_id = %s",
            (id_reserva, session["user_id"]),
        )
        conexion.commit()
        if cursor.rowcount == 0:
            return jsonify(error="No se encontró la reserva."), 404
        return jsonify(message="Reserva eliminada.")
    finally:
        conexion.close()


@app.errorhandler(Error)
def mostrar_error_mysql(error):
    app.logger.exception("No se pudo completar la operación con MySQL.")
    return jsonify(error="No se pudo completar la operación con MySQL."), 503


@app.errorhandler(RuntimeError)
def mostrar_error_configuracion(error):
    return jsonify(error=str(error)), 503


if __name__ == "__main__":
    try:
        crear_base_y_tabla()
    except (Error, RuntimeError) as error:
        print("No se pudo iniciar la aplicación:", error)
        raise SystemExit(1) from error

    if not os.getenv("SECRET_KEY"):
        app.logger.warning(
            "SECRET_KEY no está configurada; las sesiones cerrarán al reiniciar."
        )
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")))
