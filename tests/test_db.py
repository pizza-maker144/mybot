import sqlite3

import main


def get_name(db, user_id):
    conn = sqlite3.connect(db)
    row = conn.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row[0] if row else None


def test_save_user_inserts_name(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB", str(tmp_path / "test.db"))
    main.init_db()
    main.save_user(1, "Артём")

    assert get_name(main.DB, 1) == "Артём"


def test_save_user_updates_existing_name(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB", str(tmp_path / "test.db"))
    main.init_db()
    main.save_user(1, "Артём")
    main.save_user(1, "Марат")

    assert get_name(main.DB, 1) == "Марат"
