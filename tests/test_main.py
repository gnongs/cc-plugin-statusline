import io
import json
import re

from statusline import __main__ as main_mod

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _strip(s):
    return _ANSI.sub("", s)


def _run_main(monkeypatch, capsys, *, usage, stdin_data=None):
    stdin_data = stdin_data or {
        "model": {"display_name": "opus-4-7"},
        "context_window": {"used_percentage": 10},
        "workspace": {"current_dir": "/tmp"},
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    monkeypatch.setattr(main_mod, "fetch_profile", lambda: None)
    monkeypatch.setattr(main_mod, "fetch_usage", lambda: usage)
    monkeypatch.setattr(main_mod, "get_git_info", lambda cwd: (None, 0, 0, 0))
    main_mod.main()
    return _strip(capsys.readouterr().out)


def test_five_hour_99_7_displays_as_99(monkeypatch, capsys):
    """A 99.7% utilization must not be rounded up to 100% in the statusline."""
    usage = {
        "five_hour": {"utilization": 99.7, "resets_at": None},
        "seven_day": {"utilization": 0, "resets_at": None},
    }
    out = _run_main(monkeypatch, capsys, usage=usage)
    assert "99%" in out
    assert "100%" not in out


def test_five_hour_100_displays_as_100(monkeypatch, capsys):
    usage = {
        "five_hour": {"utilization": 100, "resets_at": None},
        "seven_day": {"utilization": 0, "resets_at": None},
    }
    out = _run_main(monkeypatch, capsys, usage=usage)
    assert "100%" in out


def test_seven_day_99_6_displays_as_99(monkeypatch, capsys):
    """Seven-day bucket must also cap sub-saturation at 99%."""
    usage = {
        "five_hour": {"utilization": 0, "resets_at": None},
        "seven_day": {"utilization": 99.6, "resets_at": None},
    }
    out = _run_main(monkeypatch, capsys, usage=usage)
    assert "99%" in out
    assert "100%" not in out
