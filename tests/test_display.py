from statusline.display import fmt_pct


def test_fmt_pct_floors_integers():
    assert fmt_pct(0) == 0
    assert fmt_pct(50) == 50
    assert fmt_pct(73.0) == 73


def test_fmt_pct_caps_sub_saturation_at_99():
    """Anything strictly below 100 must not round up to 100."""
    assert fmt_pct(99.0) == 99
    assert fmt_pct(99.4) == 99
    assert fmt_pct(99.5) == 99
    assert fmt_pct(99.99) == 99


def test_fmt_pct_reports_100_only_when_saturated():
    assert fmt_pct(100) == 100
    assert fmt_pct(100.0) == 100
    assert fmt_pct(150) == 100


def test_fmt_pct_handles_invalid_inputs():
    assert fmt_pct(None) == 0
    assert fmt_pct("abc") == 0
    assert fmt_pct(-5) == 0
