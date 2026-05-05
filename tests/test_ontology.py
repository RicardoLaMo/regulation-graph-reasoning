from regreason.ontology import (
    AnswerObject, ConductType, RouteTarget, OntologyConstraintValidator,
    conduct_canonical_phrases, harm_canonical_phrases,
)


def test_answer_object_to_json_roundtrip():
    a = AnswerObject(complaint_id="x", product="Mortgage", conducts=["unauthorized"], severity=3)
    d = a.to_dict()
    assert d["complaint_id"] == "x"
    assert d["product"] == "Mortgage"
    assert "evidence_spans" in d


def test_validator_severity_implies_escalation():
    a = AnswerObject(complaint_id="x", product="Mortgage", severity=5, escalation_flag=False,
                     conducts=["unauthorized"])
    v = OntologyConstraintValidator().validate(a)
    assert v.repaired.escalation_flag is True
    assert v.repaired.severity == 5


def test_validator_drops_unknown_conducts():
    a = AnswerObject(complaint_id="x", product="Mortgage", conducts=["mystery", "unauthorized"])
    v = OntologyConstraintValidator().validate(a)
    assert "mystery" not in v.repaired.conducts
    assert "unauthorized" in v.repaired.conducts


def test_validator_route_inference_from_primary_conduct():
    a = AnswerObject(complaint_id="x", product="Credit card", conducts=["unauthorized"])
    v = OntologyConstraintValidator().validate(a)
    assert v.repaired.route == RouteTarget.FRAUD_OPS.value


def test_canonical_phrases_nonempty():
    assert len(conduct_canonical_phrases()) > 30
    assert len(harm_canonical_phrases()) > 5


def test_validator_unknown_route_repaired():
    a = AnswerObject(complaint_id="x", product="Mortgage", route="some_route", conducts=["unauthorized"])
    v = OntologyConstraintValidator().validate(a)
    assert v.repaired.route in {r.value for r in RouteTarget}
