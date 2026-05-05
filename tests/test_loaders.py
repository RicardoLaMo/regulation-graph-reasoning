from regreason.io_loaders import load_complaint_sample, load_regulations, load_prebuilt_indexes


def test_load_regulations_count():
    regs = load_regulations()
    assert len(regs) >= 50
    r0 = regs[0]
    assert r0.section_id and r0.text


def test_load_prebuilt_indexes_metadata():
    idx = load_prebuilt_indexes()
    assert idx["meta"]["encoder_model"] == "all-MiniLM-L6-v2"
    assert len(idx["passages"]) == idx["meta"]["n_sections"]


def test_complaint_sample_size():
    df = load_complaint_sample(n=200, split="test")
    assert df.height >= 100
    assert "narrative" in df.columns
    assert "product" in df.columns
