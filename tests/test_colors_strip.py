from LogSmith import CPrint

def test_strip_ansi_edge_cases():
    s = "\x1b[31mRED\x1b[0m normal \x1b[1mBOLD"
    stripped = CPrint.strip_ansi(s)
    assert "RED" in stripped
    assert "normal" in stripped
    assert "BOLD" in stripped
    assert "\x1b" not in stripped
