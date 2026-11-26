import unittest
from datetime import date, timedelta
from unittest.mock import patch

import app
from werkzeug.security import check_password_hash, generate_password_hash


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        app.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.app.test_client()

    def test_trip_catalog_is_public(self):
        response = self.client.get("/api/trips")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 6)

    def test_reservations_require_login(self):
        with patch("app.conectar_a_mysql") as connect:
            response = self.client.get("/api/reservations")

        self.assertEqual(response.status_code, 401)
        connect.assert_not_called()

    def test_registration_stores_a_password_hash_and_starts_session(self):
        with patch("app.conectar_a_mysql") as connect:
            connect.return_value.cursor.return_value.lastrowid = 7
            response = self.client.post(
                "/api/register",
                json={
                    "name": "Persona de prueba",
                    "email": "Persona@Example.test",
                    "password": "password-segura",
                    "birth_date": "1990-04-15",
                    "document_number": " ab123456 ",
                    "phone": "+57 300 123 4567",
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["user"]["id"], 7)
        query, parameters = connect.return_value.cursor.return_value.execute.call_args.args
        self.assertIn("INSERT INTO users", query)
        self.assertEqual(parameters[:2], ("Persona de prueba", "persona@example.test"))
        self.assertTrue(check_password_hash(parameters[2], "password-segura"))
        self.assertEqual(parameters[3:], (date(1990, 4, 15), "AB123456", "+57 300 123 4567"))
        with self.client.session_transaction() as user_session:
            self.assertEqual(user_session["user_id"], 7)

    def test_registration_requires_birth_date_document_and_phone(self):
        with patch("app.conectar_a_mysql") as connect:
            response = self.client.post(
                "/api/register",
                json={
                    "name": "Persona de prueba",
                    "email": "persona@example.test",
                    "password": "password-segura",
                },
            )

        self.assertEqual(response.status_code, 400)
        connect.assert_not_called()

    def test_registration_rejects_a_future_birth_date(self):
        future_date = (date.today() + timedelta(days=1)).isoformat()
        with patch("app.conectar_a_mysql") as connect:
            response = self.client.post(
                "/api/register",
                json={
                    "name": "Persona de prueba",
                    "email": "persona@example.test",
                    "password": "password-segura",
                    "birth_date": future_date,
                    "document_number": "AB123456",
                    "phone": "+57 300 123 4567",
                },
            )

        self.assertEqual(response.status_code, 400)
        connect.assert_not_called()

    def test_login_starts_session_for_a_valid_password(self):
        password_hash = generate_password_hash("password-segura")
        with patch("app.conectar_a_mysql") as connect:
            connect.return_value.cursor.return_value.fetchone.return_value = (
                7,
                "Persona de prueba",
                "persona@example.test",
                password_hash,
            )
            response = self.client.post(
                "/api/login",
                json={"email": "Persona@Example.test", "password": "password-segura"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user"]["id"], 7)
        with self.client.session_transaction() as user_session:
            self.assertEqual(user_session["user_id"], 7)

    def test_login_rejects_an_incorrect_password(self):
        with patch("app.conectar_a_mysql") as connect:
            connect.return_value.cursor.return_value.fetchone.return_value = (
                7,
                "Persona de prueba",
                "persona@example.test",
                generate_password_hash("password-segura"),
            )
            response = self.client.post(
                "/api/login",
                json={"email": "persona@example.test", "password": "incorrecta"},
            )

        self.assertEqual(response.status_code, 401)
        with self.client.session_transaction() as user_session:
            self.assertNotIn("user_id", user_session)

    def test_quote_uses_server_trip_price(self):
        quote = app.validar_datos_reserva({
            "trip_id": "tokyo",
            "customer_name": "Persona de prueba",
            "customer_email": "persona@example.test",
            "departure_date": (date.today() + timedelta(days=1)).isoformat(),
            "travelers": "3",
        })

        self.assertEqual(quote["total"], 4350)

    def test_quote_rejects_past_departure(self):
        with self.assertRaisesRegex(ValueError, "pasado"):
            app.validar_datos_reserva({
                "trip_id": "paris",
                "customer_name": "Persona de prueba",
                "customer_email": "persona@example.test",
                "departure_date": (date.today() - timedelta(days=1)).isoformat(),
                "travelers": "1",
            })

    def test_invalid_reservation_input_does_not_query_database(self):
        with self.client.session_transaction() as user_session:
            user_session["user_id"] = 1

        with patch("app.conectar_a_mysql") as connect:
            response = self.client.post("/api/reservations", data="not json")

        self.assertEqual(response.status_code, 400)
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
