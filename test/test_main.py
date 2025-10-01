import contextlib
import io
import sys
from unittest import mock

from _pytest.monkeypatch import MonkeyPatch

import src.main

# TODO: fix all of these tests


def make_mock_config(tablebase_available: bool = True) -> mock.Mock:
    """Create a mock EngineConfig with specified tablebase availability."""
    cfg = mock.Mock()
    cfg.engine_path = "/fake/engine"
    cfg.threads = 4
    cfg.hash_size = 1024
    cfg.skill_level = 20
    cfg.eval_depth = 18
    cfg.syzygy_path = "/fake/tablebase" if tablebase_available else ""

    return cfg


def test_main_with_tablebase(monkeypatch: MonkeyPatch) -> None:
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


def test_main_without_tablebase(monkeypatch: MonkeyPatch) -> None:
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


def test_main_cleanup(monkeypatch: MonkeyPatch) -> None:
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


def test_main_entry_point(monkeypatch: MonkeyPatch) -> None:
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
        file_path = sys.modules["src.main"].__file__

        if not isinstance(file_path, str):
            raise RuntimeError("src.main.__file__ is not set")

        exec(open(file_path).read(), src.main.__dict__)
