from tools.calculator import calculate_delay

def test_delay():
    result = calculate_delay("2026-01-01 10:00", "2026-01-01 13:00")
    assert result["delay_hours"] == 3
