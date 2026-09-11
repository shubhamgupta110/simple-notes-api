
from flask import Flask, request, jsonify
import secrets
from functools import wraps

from database import get_db_connection, init_db

app = Flask(__name__)

init_db()


# Token Authentication
def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.headers.get("Authorization")

        if not token:
            return jsonify({
                "error": "Authentication token is required"
            }), 401

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE token = ?",
            (token,)
        ).fetchone()

        conn.close()

        if not user:
            return jsonify({
                "error": "Invalid authentication token"
            }), 401

        return f(*args, **kwargs)

    return decorated


@app.route("/")
def home():
    return jsonify({
        "message": "Simple Notes API is running"
    })


@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    token = secrets.token_hex(16)

    conn.execute(
        "UPDATE users SET token = ? WHERE id = ?",
        (token, user["id"])
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Login successful",
        "token": token
    })


@app.route("/notes", methods=["GET"])
@token_required
def get_notes():

    conn = get_db_connection()

    notes = conn.execute(
        "SELECT * FROM notes"
    ).fetchall()

    conn.close()

    return jsonify([
        dict(note) for note in notes
    ])


@app.route("/notes", methods=["POST"])
@token_required
def add_note():

    data = request.get_json()

    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        return jsonify({
            "error": "Title and content are required"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (title, content)
    )

    conn.commit()

    note_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "message": "Note created successfully",
        "id": note_id
    }), 201


@app.route("/notes/<int:note_id>", methods=["DELETE"])
@token_required
def delete_note(note_id):

    conn = get_db_connection()

    cursor = conn.execute(
        "DELETE FROM notes WHERE id = ?",
        (note_id,)
    )

    conn.commit()

    conn.close()

    if cursor.rowcount == 0:
        return jsonify({
            "error": "Note not found"
        }), 404

    return jsonify({
        "message": "Note deleted successfully"
    })


if __name__ == "__main__":
    app.run(debug=True)

