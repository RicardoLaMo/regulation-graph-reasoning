import os
import pytest
from regreason.config import CFG


@pytest.mark.slow
def test_extractor_finds_unauthorized_when_phrase_present():
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from regreason.extract import build_extractor, extract_answer_object
    state = build_extractor()
    text = "Someone made an unauthorized transaction on my debit card; I lost money."
    a = extract_answer_object(text, "c1", "Credit card", "fraud", state)
    assert "unauthorized" in a.conducts
    assert "monetary_loss" in a.harms
    assert a.route == "fraud_ops"
