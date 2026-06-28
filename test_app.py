"""
个人待办事项小程序 - 单元测试
"""
import os
import json
import pytest
import sys

sys.path.insert(0, os.path.dirname(__file__))
from app import app, init_db, DATABASE

TEST_DB = os.path.join(os.path.dirname(__file__), "test_todo.db")


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Use test database
    original_db = DATABASE
    import app as app_module
    app_module.DATABASE = TEST_DB
    init_db()
    with app.test_client() as client:
        yield client
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    app_module.DATABASE = original_db


class TestTodoCRUD:
    def test_create_todo(self, client):
        resp = client.post("/api/todos", json={"title": "Test task", "priority": "high"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["message"] == "Created"
        assert "id" in data

    def test_create_todo_no_title(self, client):
        resp = client.post("/api/todos", json={"priority": "low"})
        assert resp.status_code == 400

    def test_get_todos(self, client):
        client.post("/api/todos", json={"title": "Task 1"})
        client.post("/api/todos", json={"title": "Task 2"})
        resp = client.get("/api/todos")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2

    def test_get_todo_by_id(self, client):
        client.post("/api/todos", json={"title": "Find me"})
        resp = client.get("/api/todos/1")
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Find me"

    def test_get_todo_not_found(self, client):
        resp = client.get("/api/todos/999")
        assert resp.status_code == 404

    def test_update_todo(self, client):
        client.post("/api/todos", json={"title": "Original"})
        resp = client.put("/api/todos/1", json={"title": "Updated", "completed": 1})
        assert resp.status_code == 200
        resp = client.get("/api/todos/1")
        assert resp.get_json()["title"] == "Updated"
        assert resp.get_json()["completed"] == 1

    def test_delete_todo(self, client):
        client.post("/api/todos", json={"title": "Delete me"})
        resp = client.delete("/api/todos/1")
        assert resp.status_code == 200
        resp = client.get("/api/todos")
        assert len(resp.get_json()) == 0

    def test_filter_by_category(self, client):
        client.post("/api/categories", json={"name": "Work"})
        client.post("/api/todos", json={"title": "Work task", "category_id": 1})
        resp = client.get("/api/todos?category_id=1")
        assert len(resp.get_json()) == 1

    def test_search_keyword(self, client):
        client.post("/api/todos", json={"title": "Buy milk"})
        client.post("/api/todos", json={"title": "Buy coffee"})
        resp = client.get("/api/todos?keyword=coffee")
        assert len(resp.get_json()) == 1


class TestCategoryCRUD:
    def test_get_categories(self, client):
        resp = client.get("/api/categories")
        assert resp.status_code == 200
        assert len(resp.get_json()) >= 3  # default categories

    def test_create_category(self, client):
        resp = client.post("/api/categories", json={"name": "New Cat"})
        assert resp.status_code == 201

    def test_duplicate_category(self, client):
        client.post("/api/categories", json={"name": "Dup"})
        resp = client.post("/api/categories", json={"name": "Dup"})
        assert resp.status_code == 409


class TestStats:
    def test_stats(self, client):
        client.post("/api/todos", json={"title": "T1", "priority": "high"})
        client.post("/api/todos", json={"title": "T2", "priority": "low"})
        resp = client.get("/api/stats")
        data = resp.get_json()
        assert data["total"] == 2
        assert data["completed"] == 0
        assert data["pending"] == 2
