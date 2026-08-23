from retrieval.ingest import source_metadata

def test_deprecated_lower_authority():
    meta = source_metadata("02_Support_Policy_v2_DEPRECATED.pdf")
    assert meta["authority"] < 4
    assert meta["status"] == "deprecated"

def test_agreement_high_authority():
    meta = source_metadata("05_Northstar_Logistics_Enterprise_Agreement.pdf")
    assert meta["authority"] == 5
