# Aplicación de viajes

Aplicación educativa hecha con Python, Flask, MySQL, HTML, CSS y JavaScript.
Permite crear una cuenta, cotizar viajes y administrar reservas propias.

## Ejecutar con Docker

1. Instala y abre Docker Desktop.
2. Si no tienes `.env`, copia `.env.example` con ese nombre. Si ya existe,
   consérvalo; no reemplaces tus datos locales de Laragon. No compartas ni subas
   `.env`.
3. Inicia MySQL desde Laragon y revisa que `.env` tenga las credenciales
   correctas (`MYSQL_USER`, `MYSQL_PASSWORD` y `MYSQL_DATABASE`). Docker usa
   `host.docker.internal` para conectarse al MySQL de Windows. Si quieres
   valores distintos para Docker, configura las variables `DOCKER_MYSQL_*`.
4. En `.env`, configura `DOCKER_APP_SECRET_KEY` con una clave larga propia.
5. Desde una terminal abierta en esta carpeta, inicia la aplicación:

   ```powershell
   docker compose up --build
   ```

6. Abre `http://localhost:5000` en el navegador. La aplicación crea la base y
   las tablas necesarias en el MySQL de Laragon. Las cuentas y reservas quedan
   guardadas allí.

Para detenerla, pulsa `Ctrl+C` y ejecuta `docker compose down`. Esto no elimina
la base ni las cuentas guardadas en Laragon.

## Conexión con Laragon

Compose ya usa `host.docker.internal` para conectar el contenedor a MySQL en
Windows. Si necesitas personalizar la conexión, configura estas variables:

```dotenv
DOCKER_MYSQL_HOST=host.docker.internal
DOCKER_MYSQL_PORT=3306
DOCKER_MYSQL_USER=root
DOCKER_MYSQL_PASSWORD=
DOCKER_MYSQL_DATABASE=viajes_app
```

La aplicación debe poder conectarse a MySQL desde Docker Desktop. Si Laragon
solo acepta conexiones locales, permite conexiones desde Docker en la
configuración de MySQL y el firewall. La cuenta de MySQL debe tener permisos
para crear la base y sus tablas.

## Ejecutar directamente con Python y Laragon

1. Inicia MySQL desde Laragon.
2. Copia `.env.example` como `.env` solo si aún no tienes un `.env`. Si ya
   existe, consérvalo y revisa `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`,
   `MYSQL_PASSWORD`, `MYSQL_DATABASE` y `SECRET_KEY`.
3. Instala dependencias e inicia la aplicación:

   ```powershell
   python -m pip install -r requirements.txt
   python app.py
   ```

4. Abre `http://127.0.0.1:5000` en el navegador.

Al iniciar, la aplicación crea las tablas que faltan y agrega los campos de
cuenta y perfil a instalaciones anteriores. Las cuentas antiguas se conservan;
los nuevos campos del perfil se solicitan al crear cuentas nuevas.

Para ejecutar las pruebas básicas de validación:

```powershell
python -m unittest discover -s tests -v
```

## Módulos

- Registro e inicio de sesión con nombre, fecha de nacimiento, documento,
  teléfono y correo; las contraseñas se almacenan como hash.
- Saludo según la hora local y el nombre de la cuenta.
- Catálogo de destinos y cotizador por destino y número de viajeros.
- Creación, consulta, edición y eliminación de reservas propias.
- Simulación de pago por tarjeta o PSE, sin capturar datos bancarios ni hacer
  cobros reales. La base guarda solo el método, el valor y el estado de prueba.
- Ticket de demostración después de aprobar la simulación.

Para aceptar pagos reales se debe integrar una pasarela de pago y guardar solo
su referencia y estado de transacción; no se deben guardar números de tarjeta,
códigos de seguridad ni credenciales bancarias en esta aplicación.

## Capturas para la guía

La [guía PDF](./Guia_actualizada_viajes.pdf) incluye las capturas compartidas.
Los archivos de imagen que utiliza la versión HTML de la guía están en
`capturas_guia/`.
