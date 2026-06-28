"""
个人待办事项小程序
Flask + SQLite RESTful API
"""
import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), "todo.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            completed INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low','medium','high')),
            category_id INTEGER,
            due_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    """)
    # Insert default categories if empty
    count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO categories (name) VALUES (?)", ("工作",))
        conn.execute("INSERT INTO categories (name) VALUES (?)", ("学习",))
        conn.execute("INSERT INTO categories (name) VALUES (?)", ("生活",))
    conn.commit()
    conn.close()


# ======== Todo CRUD ========

@app.route("/api/todos", methods=["GET"])
def get_todos():
    db = get_db()
    category_id = request.args.get("category_id")
    completed = request.args.get("completed")
    keyword = request.args.get("keyword")

    query = "SELECT t.*, c.name as category_name FROM todos t LEFT JOIN categories c ON t.category_id = c.id WHERE 1=1"
    params = []

    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if completed is not None:
        query += " AND t.completed = ?"
        params.append(int(completed))
    if keyword:
        query += " AND (t.title LIKE ? OR t.description LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    query += " ORDER BY t.created_at DESC"
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    db = get_db()
    row = db.execute(
        "SELECT t.*, c.name as category_name FROM todos t LEFT JOIN categories c ON t.category_id = c.id WHERE t.id = ?",
        (todo_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(dict(row))


@app.route("/api/todos", methods=["POST"])
def create_todo():
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify({"error": "Title is required"}), 400

    db = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "INSERT INTO todos (title, description, priority, category_id, due_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data["title"], data.get("description", ""), data.get("priority", "medium"),
         data.get("category_id"), data.get("due_date"), now, now)
    )
    db.commit()
    todo_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return jsonify({"message": "Created", "id": todo_id}), 201


@app.route("/api/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json()
    db = get_db()
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Todo not found"}), 404

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        """UPDATE todos SET title=?, description=?, completed=?, priority=?,
           category_id=?, due_date=?, updated_at=? WHERE id=?""",
        (data.get("title", row["title"]), data.get("description", row["description"]),
         int(data.get("completed", row["completed"])), data.get("priority", row["priority"]),
         data.get("category_id"), data.get("due_date"), now, todo_id)
    )
    db.commit()
    return jsonify({"message": "Updated", "id": todo_id})


@app.route("/api/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    db = get_db()
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Todo not found"}), 404
    db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    return jsonify({"message": "Deleted", "id": todo_id})


# ======== Category CRUD ========

@app.route("/api/categories", methods=["GET"])
def get_categories():
    db = get_db()
    rows = db.execute("SELECT * FROM categories ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/categories", methods=["POST"])
def create_category():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400
    db = get_db()
    try:
        db.execute("INSERT INTO categories (name) VALUES (?)", (data["name"],))
        db.commit()
        return jsonify({"message": "Created"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Category already exists"}), 409


@app.route("/api/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    db.commit()
    return jsonify({"message": "Deleted"})


# ======== Stats ========

@app.route("/api/stats", methods=["GET"])
def get_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    done = db.execute("SELECT COUNT(*) FROM todos WHERE completed=1").fetchone()[0]
    pending = total - done
    by_priority = db.execute("""
        SELECT priority, COUNT(*) as cnt FROM todos GROUP BY priority
    """).fetchall()
    return jsonify({
        "total": total, "completed": done, "pending": pending,
        "by_priority": {r["priority"]: r["cnt"] for r in by_priority}
    })


@app.route("/")
def index():
    return jsonify({"message": "Todo App API", "endpoints": [
        "GET /api/todos", "POST /api/todos", "GET /api/todos/<id>",
        "PUT /api/todos/<id>", "DELETE /api/todos/<id>",
        "GET /api/categories", "POST /api/categories", "DELETE /api/categories/<id>",
        "GET /api/stats"
    ]})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
