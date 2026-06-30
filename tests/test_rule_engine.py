from dynamic_alert.services.rule_engine import OPERATORS


def test_supported_operators() -> None:
    assert OPERATORS[">"](71.3, 70.0) is True
    assert OPERATORS["<"](2.0, 3.0) is True
    assert OPERATORS["=="](5.0, 5.0) is True
