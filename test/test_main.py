import contextlib
import io
import sys
import types
from unittest import mock

import pytest

import src.main


def make_mock_config(tablebase_available=True):
    cfg = mock.Mock()
    cfg.engine_path = "/fake/engine"
    cfg.threads = 4
    cfg.hash_size = 1024
    cfg.skill_level = 20
    cfg.eval_depth = 18
    cfg.syzygy_path = "/fake/tablebase" if tablebase_available else ""

    return cfg


def test_main_with_tablebase(monkeypatch):
    # Patch all dependencies
    mock_config = make_mock_config(tablebase_available=True)

    monkeypatch.setattr(
        src.main.config, "parse_config", mock.Mock(return_value=mock_config)
    )

    monkeypatch.setattr(
        src.main.engine_handler,
        "get_engine",
        mock.Mock(return_value=mock.Mock(quit=mock.Mock())),
    )

    mock_tablebase = mock.Mock(close=mock.Mock())
    monkeypatch.setattr(
        src.main.engine_handler,
        "get_syzygy_tablebase",
        mock.Mock(return_value=mock_tablebase),
    )

    monkeypatch.setattr(src.main.game_logic, "play_game", mock.Mock())
    monkeypatch.setattr(src.main.board_ui, "print_game_over_info", mock.Mock())
    monkeypatch.setattr(src.main.board_ui, "print_tablebase_info", mock.Mock())

    # Capture output
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.main.main()
        output = buf.getvalue()

    assert "Tablebases loaded" in output


def test_main_without_tablebase(monkeypatch):
    mock_config = make_mock_config(tablebase_available=False)

    monkeypatch.setattr(
        src.main.config, "parse_config", mock.Mock(return_value=mock_config)
    )

    monkeypatch.setattr(
        src.main.engine_handler,
        "get_engine",
        mock.Mock(return_value=mock.Mock(quit=mock.Mock())),
    )

    monkeypatch.setattr(
        src.main.engine_handler,
        "get_syzygy_tablebase",
        mock.Mock(return_value=None),
    )

    monkeypatch.setattr(src.main.game_logic, "play_game", mock.Mock())
    monkeypatch.setattr(src.main.board_ui, "print_game_over_info", mock.Mock())
    monkeypatch.setattr(src.main.board_ui, "print_tablebase_info", mock.Mock())

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.main.main()
        output = buf.getvalue()

    assert "Tablebases not available" in output


def test_main_cleanup(monkeypatch):
    # Ensure engine.quit and tablebase.close are always called
    mock_config = make_mock_config(tablebase_available=True)
    monkeypatch.setattr(
        src.main.config, "parse_config", mock.Mock(return_value=mock_config)
    )

    engine = mock.Mock(quit=mock.Mock())
    monkeypatch.setattr(
        src.main.engine_handler, "get_engine", mock.Mock(return_value=engine)
    )

    tablebase = mock.Mock(close=mock.Mock())
    monkeypatch.setattr(
        src.main.engine_handler,
        "get_syzygy_tablebase",
        mock.Mock(return_value=tablebase),
    )

    monkeypatch.setattr(src.main.game_logic, "play_game", mock.Mock())
    monkeypatch.setattr(src.main.board_ui, "print_game_over_info", mock.Mock())
    monkeypatch.setattr(src.main.board_ui, "print_tablebase_info", mock.Mock())
    src.main.main()
    engine.quit.assert_called_once()
    tablebase.close.assert_called_once()


def test_main_entry_point(monkeypatch):
    monkeypatch.setattr(
        src.main.config,
        "parse_config",
        mock.Mock(return_value=make_mock_config()),
    )

    monkeypatch.setattr(
        src.main.engine_handler,
        "get_engine",
        mock.Mock(return_value=mock.Mock(quit=mock.Mock())),
    )

    monkeypatch.setattr(
        src.main.engine_handler,
        "get_syzygy_tablebase",
        mock.Mock(return_value=None),
    )

    monkeypatch.setattr(src.main.game_logic, "play_game", mock.Mock())
    monkeypatch.setattr(src.main.board_ui, "print_game_over_info", mock.Mock())
    monkeypatch.setattr(src.main.board_ui, "print_tablebase_info", mock.Mock())

    # Simulate running as __main__ with clean argv
    monkeypatch.setattr(src.main, "__name__", "__main__")
    monkeypatch.setattr(sys, "argv", ["src/main.py"])

    # Capture output to avoid printing during test
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        exec(open(sys.modules["src.main"].__file__).read(), src.main.__dict__)
