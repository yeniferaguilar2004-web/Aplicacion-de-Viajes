import unittest
from datetime import date, timedelta
from unittest.mock import patch

import app


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
