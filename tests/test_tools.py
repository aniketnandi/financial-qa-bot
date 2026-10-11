from tools import calculate_growth, calculate_margin


def test_growth_matches_tesla_fy2023_revenue():
    # 96,773 vs 81,462 ($M), from the FY2023 10-K
    assert calculate_growth(96773, 81462) == "18.80%"


def test_growth_handles_decline_and_zero_base():
    assert calculate_growth(50, 100) == "-50.00%"
    assert calculate_growth(10, 0).startswith("Cannot calculate growth")


def test_margin():
    assert calculate_margin(17660, 96773) == "18.25%"
    assert calculate_margin(1, 0).startswith("Cannot calculate margin")
