from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database" / "data" / "drive847.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


class Handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        return json.loads(body.decode("utf-8"))

    def do_GET(self):

        if self.path == "/":
            self.send_json(200, {
                "project": "Drive 847",
                "status": "online",
                "version": "0.4.0"
            })
            return

        if self.path == "/api/records":

            connection = get_connection()

            rows = connection.execute("""
                SELECT id, nombre, estado, created_at
                FROM records
                ORDER BY id DESC
            """).fetchall()

            connection.close()

            records = [
                {
                    "id": row[0],
                    "nombre": row[1],
                    "estado": row[2],
                    "created_at": row[3]
                }
                for row in rows
            ]

            self.send_json(200, {
                "total": len(records),
                "records": records
            })
            return

        self.send_json(404, {
            "error": "Ruta no encontrada"
        })

    def do_POST(self):

        if self.path != "/api/records":
            self.send_json(404, {
                "error": "Ruta no encontrada"
            })
            return

        try:

            data = self.read_json()

            nombre = data.get("nombre")
            estado = data.get("estado", "activo")

            if not nombre:
                self.send_json(400, {
                    "error": "El campo nombre es obligatorio"
                })
                return

            connection = get_connection()

            cursor = connection.execute(
                """
                INSERT INTO records (nombre, estado)
                VALUES (?, ?)
                """,
                (nombre, estado)
            )

            connection.commit()

            record_id = cursor.lastrowid

            connection.close()

            self.send_json(201, {
                "id": record_id,
                "nombre": nombre,
                "estado": estado
            })

        except Exception as error:

            self.send_json(500, {
                "error": str(error)
            })

    def do_PUT(self):

        try:

            if not self.path.startswith("/api/records/"):
                self.send_json(404, {
                    "error": "Ruta no encontrada"
                })
                return

            record_id = int(self.path.split("/")[-1])
            data = self.read_json()

            nombre = data.get("nombre")
            estado = data.get("estado")

            if not nombre:
                self.send_json(400, {
                    "error": "El campo nombre es obligatorio"
                })
                return

            connection = get_connection()

            cursor = connection.execute(
                """
                UPDATE records
                SET nombre = ?, estado = ?
                WHERE id = ?
                """,
                (nombre, estado, record_id)
            )

            connection.commit()

            if cursor.rowcount == 0:
                connection.close()

                self.send_json(404, {
                    "error": "Registro no encontrado"
                })
                return

            connection.close()

            self.send_json(200, {
                "id": record_id,
                "nombre": nombre,
                "estado": estado
            })

        except Exception as error:

            self.send_json(500, {
                "error": str(error)
            })

    def do_DELETE(self):

        try:

            if not self.path.startswith("/api/records/"):
                self.send_json(404, {
                    "error": "Ruta no encontrada"
                })
                return

            record_id = int(self.path.split("/")[-1])

            connection = get_connection()

            cursor = connection.execute(
                """
                DELETE FROM records
                WHERE id = ?
                """,
                (record_id,)
            )

            connection.commit()

            if cursor.rowcount == 0:
                connection.close()

                self.send_json(404, {
                    "error": "Registro no encontrado"
                })
                return

            connection.close()

            self.send_json(200, {
                "message": "Registro eliminado",
                "id": record_id
            })

        except Exception as error:

            self.send_json(500, {
                "error": str(error)
            })


if __name__ == "__main__":

    server = HTTPServer(("localhost", 8470), Handler)

    print("================================")
    print(" DRIVE 847 BACKEND v0.4.0")
    print(" http://localhost:8470")
    print("================================")

    server.serve_forever()
