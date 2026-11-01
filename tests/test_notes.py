import main


def setup_db(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB", str(tmp_path / "test.db"))
    main.init_db()


def test_add_and_get_notes(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)

    first = main.add_note(1, "купить хлеб")
    second = main.add_note(1, "позвонить маме")

    assert first != second
    assert main.get_notes(1) == [(first, "купить хлеб"), (second, "позвонить маме")]


def test_notes_are_per_user(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)

    main.add_note(1, "заметка первого")
    main.add_note(2, "заметка второго")

    assert main.get_notes(1) == [(1, "заметка первого")]
    assert main.get_notes(2) == [(2, "заметка второго")]


def test_delete_note(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    note_id = main.add_note(1, "удалить меня")

    assert main.delete_note(1, note_id) is True
    assert main.get_notes(1) == []
    assert main.delete_note(1, note_id) is False


def test_cannot_delete_other_users_note(tmp_path, monkeypatch):
    setup_db(tmp_path, monkeypatch)
    note_id = main.add_note(1, "чужая")

    assert main.delete_note(2, note_id) is False
    assert main.get_notes(1) == [(note_id, "чужая")]
