"""CFPB-flavored ontology: enums, AnswerObject schema, validator, canonical phrases."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import List, Optional, Tuple


class ConductType(str, Enum):
    UNAUTHORIZED = "unauthorized"
    DECEPTIVE_PRACTICE = "deceptive_practice"
    UNFAIR_FEE = "unfair_fee"
    DEBT_COLLECTION_ABUSE = "debt_collection_abuse"
    CREDIT_REPORT_ERROR = "credit_report_error"
    LOAN_SERVICING_ERROR = "loan_servicing_error"
    DISCRIMINATION = "discrimination"
    DARK_PATTERN = "dark_pattern"
    IDENTITY_FAILURE = "identity_failure"
    CRYPTO_LOSS = "crypto_loss"
    AI_HARM = "ai_harm"


class HarmType(str, Enum):
    MONETARY_LOSS = "monetary_loss"
    CREDIT_DAMAGE = "credit_damage"
    DENIAL_OF_SERVICE = "denial_of_service"
    PRIVACY_VIOLATION = "privacy_violation"
    EMOTIONAL_DISTRESS = "emotional_distress"
    DISCRIMINATION_HARM = "discrimination_harm"


class ObligationType(str, Enum):
    DISCLOSURE = "disclosure"
    INVESTIGATION = "investigation"
    REIMBURSEMENT = "reimbursement"
    NOTICE_OF_RIGHTS = "notice_of_rights"
    DATA_CORRECTION = "data_correction"
    NON_DISCRIMINATION = "non_discrimination"
    COMPLAINT_RESPONSE = "complaint_response"


class SeverityLevel(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class RouteTarget(str, Enum):
    FRAUD_OPS = "fraud_ops"
    LEGAL = "legal"
    SUPERVISOR = "supervisor"
    COLLECTIONS = "collections"
    SERVICING = "servicing"
    ROUTE_TO_OTHER = "route_to_other"


CONDUCT_PHRASES = {
    ConductType.UNAUTHORIZED: [
        "unauthorized transaction", "did not authorize", "someone used my card",
        "without my permission", "fraudulent charge", "stolen funds",
    ],
    ConductType.DECEPTIVE_PRACTICE: [
        "misleading advertising", "false promises", "bait and switch",
        "told me one thing did another", "deceptive disclosure", "hidden terms",
    ],
    ConductType.UNFAIR_FEE: [
        "surprise fee", "junk fee", "excessive overdraft", "hidden charge",
        "late fee charged unfairly", "unexpected charge",
    ],
    ConductType.DEBT_COLLECTION_ABUSE: [
        "harassing phone calls", "calls late at night", "threatening letter",
        "debt collector calling repeatedly", "collection agency abusive",
    ],
    ConductType.CREDIT_REPORT_ERROR: [
        "incorrect on credit report", "dispute not investigated",
        "wrong account on credit", "credit bureau wont fix", "inaccurate tradeline",
    ],
    ConductType.LOAN_SERVICING_ERROR: [
        "payment misapplied", "escrow shortage error", "loan servicer mistake",
        "mortgage payment lost", "servicer applied wrong",
    ],
    ConductType.DISCRIMINATION: [
        "denied because of race", "discrimination based on", "redlining",
        "disparate treatment", "fair lending violation",
    ],
    ConductType.DARK_PATTERN: [
        "couldnt cancel subscription", "trick design", "dark pattern",
        "hidden cancel button", "forced auto renewal",
    ],
    ConductType.IDENTITY_FAILURE: [
        "identity theft", "imposter opened account", "ssn used by someone",
        "synthetic identity", "fake account in my name",
    ],
    ConductType.CRYPTO_LOSS: [
        "crypto wallet drained", "lost bitcoin", "crypto exchange froze",
        "lost ethereum", "stablecoin depegged",
    ],
    ConductType.AI_HARM: [
        "ai chatbot gave wrong info", "robo advisor mistake",
        "algorithm denied me", "ai model wrong decision", "automated denial",
    ],
}

HARM_PHRASES = {
    HarmType.MONETARY_LOSS: ["lost money", "stolen funds", "out of pocket", "financial loss"],
    HarmType.CREDIT_DAMAGE: ["credit score dropped", "credit damaged", "denied credit because"],
    HarmType.DENIAL_OF_SERVICE: ["account closed", "denied loan", "refused to open"],
    HarmType.PRIVACY_VIOLATION: ["personal info exposed", "data leaked", "privacy breach"],
    HarmType.EMOTIONAL_DISTRESS: ["stressed", "anxiety", "humiliated", "embarrassed"],
    HarmType.DISCRIMINATION_HARM: ["denied because of", "treated differently"],
}


CONDUCT_TO_ROUTE = {
    ConductType.UNAUTHORIZED: RouteTarget.FRAUD_OPS,
    ConductType.IDENTITY_FAILURE: RouteTarget.FRAUD_OPS,
    ConductType.CRYPTO_LOSS: RouteTarget.FRAUD_OPS,
    ConductType.DECEPTIVE_PRACTICE: RouteTarget.LEGAL,
    ConductType.DISCRIMINATION: RouteTarget.LEGAL,
    ConductType.DARK_PATTERN: RouteTarget.LEGAL,
    ConductType.DEBT_COLLECTION_ABUSE: RouteTarget.COLLECTIONS,
    ConductType.LOAN_SERVICING_ERROR: RouteTarget.SERVICING,
    ConductType.CREDIT_REPORT_ERROR: RouteTarget.SERVICING,
    ConductType.UNFAIR_FEE: RouteTarget.SUPERVISOR,
    ConductType.AI_HARM: RouteTarget.SUPERVISOR,
}


@dataclass
class EvidenceSpan:
    passage_id: str            # complaint id (with offsets) or regulation section id
    char_start: int
    char_end: int
    score: float
    source: str                # "complaint" or "regulation"
    text: str = ""


@dataclass
class AnswerObject:
    complaint_id: str
    product: str
    issue: str = ""
    conducts: List[str] = field(default_factory=list)
    harms: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    severity: int = 1
    route: str = RouteTarget.ROUTE_TO_OTHER.value
    confidence: float = 0.0
    ood_score: float = 0.0
    escalation_flag: bool = False
    evidence_spans: List[EvidenceSpan] = field(default_factory=list)
    retrieved_passage_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["evidence_spans"] = [asdict(s) for s in self.evidence_spans]
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


@dataclass
class ValidationResult:
    valid: bool
    repaired: AnswerObject
    violations: List[str]


class OntologyConstraintValidator:
    """Cross-field rule enforcement with auto-repair."""

    def validate(self, ans: AnswerObject) -> ValidationResult:
        violations: List[str] = []
        repaired = AnswerObject(**{**ans.__dict__})
        repaired.evidence_spans = list(ans.evidence_spans)

        # 1. severity bounds
        if not (1 <= repaired.severity <= 5):
            violations.append(f"severity out-of-range: {repaired.severity}")
            repaired.severity = max(1, min(5, repaired.severity))

        # 2. severity >= 4 implies escalation
        if repaired.severity >= 4 and not repaired.escalation_flag:
            violations.append("severity>=4 should imply escalation_flag=True")
            repaired.escalation_flag = True

        # 3. conducts ⊆ ConductType
        valid_conducts = {c.value for c in ConductType}
        bad = [c for c in repaired.conducts if c not in valid_conducts]
        if bad:
            violations.append(f"unknown conducts dropped: {bad}")
            repaired.conducts = [c for c in repaired.conducts if c in valid_conducts]

        # 4. harms ⊆ HarmType
        valid_harms = {h.value for h in HarmType}
        bad_h = [h for h in repaired.harms if h not in valid_harms]
        if bad_h:
            violations.append(f"unknown harms dropped: {bad_h}")
            repaired.harms = [h for h in repaired.harms if h in valid_harms]

        # 5. route ∈ RouteTarget
        valid_routes = {r.value for r in RouteTarget}
        if repaired.route not in valid_routes:
            violations.append(f"unknown route '{repaired.route}' -> route_to_other")
            repaired.route = RouteTarget.ROUTE_TO_OTHER.value

        # 6. crypto/AI flag coherence -- if conduct says crypto, harms should include monetary_loss
        if (ConductType.CRYPTO_LOSS.value in repaired.conducts
                and HarmType.MONETARY_LOSS.value not in repaired.harms):
            violations.append("crypto_loss conduct lacks monetary_loss harm; auto-adding")
            repaired.harms.append(HarmType.MONETARY_LOSS.value)

        # 7. route consistent with primary conduct (if any)
        if repaired.conducts:
            primary = repaired.conducts[0]
            try:
                expected = CONDUCT_TO_ROUTE[ConductType(primary)].value
                if repaired.route == RouteTarget.ROUTE_TO_OTHER.value:
                    repaired.route = expected
            except (ValueError, KeyError):
                pass

        # 8. confidence bound
        if not (0.0 <= repaired.confidence <= 1.0):
            violations.append(f"confidence out-of-range: {repaired.confidence}")
            repaired.confidence = max(0.0, min(1.0, repaired.confidence))

        return ValidationResult(valid=(len(violations) == 0), repaired=repaired, violations=violations)


def conduct_canonical_phrases() -> List[Tuple[ConductType, str]]:
    out: List[Tuple[ConductType, str]] = []
    for c, phrases in CONDUCT_PHRASES.items():
        for p in phrases:
            out.append((c, p))
    return out


def harm_canonical_phrases() -> List[Tuple[HarmType, str]]:
    out: List[Tuple[HarmType, str]] = []
    for h, phrases in HARM_PHRASES.items():
        for p in phrases:
            out.append((h, p))
    return out
