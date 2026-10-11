import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))

from eval_qa import check_numeric, is_refusal  # noqa: E402

PCT = {"value": 15.47, "unit": "percent", "abs_tol": 0.5}
USD = {"value": 96773000000, "unit": "usd", "rel_tol": 0.01}


def test_percent_plain_and_latex():
    assert check_numeric("Net margin was 15.47%.", PCT)
    assert check_numeric(r"$$\mathbf{15.47\%}$$", PCT)
    assert not check_numeric("Net margin was 18.25%.", PCT)


def test_dollar_amounts_in_millions_and_billions():
    assert check_numeric("Total revenues were $96,773 million.", USD)
    assert check_numeric("Revenue was about $96.8 billion.", USD)
    assert not check_numeric("Revenue was $81,462 million.", USD)


def test_refusal_detection():
    assert is_refusal("I could not find this information in the provided documents.")
    assert not is_refusal("Revenue was $96,773 million.")
