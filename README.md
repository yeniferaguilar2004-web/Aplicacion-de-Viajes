# Aplicación de viajes

Aplicación educativa hecha con Python, Flask, MySQL, HTML, CSS y JavaScript.
Permite crear una cuenta, cotizar viajes y administrar reservas propias.

## Preparar MySQL con Laragon

1. Inicia MySQL desde Laragon.
2. Si no tienes `.env`, copia `.env.example` con ese nombre. Si ya existe,
   consérvalo y agrega `SECRET_KEY` con un valor aleatorio largo; no reemplaces
   tus datos de conexión. No compartas ni subas `.env`.
4. Instala los paquetes desde una terminal abierta en esta carpeta:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Inicia la aplicación:

   ```powershell
   python app.py
   ```

6. Abre `http://127.0.0.1:5000` en el navegador.

Al iniciar, la aplicación crea las tablas que faltan y agrega el campo de cuenta
a la tabla de reservas existente. Las reservas antiguas quedan conservadas, pero
sin una cuenta asignada no se muestran en la lista privada de ningún usuario.

Para ejecutar las pruebas básicas de validación:

```powershell
python -m unittest discover -s tests -v
```

## Módulos

- Registro e inicio de sesión con contraseñas almacenadas como hash.
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
