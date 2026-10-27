from app.schemas import TransactionRequest, RiskAssessment

def assess_risk(tx: TransactionRequest) -> RiskAssessment:
    """
    Transparent demo rules, NOT a validated fraud model.
    In a production system, replace this with a versioned model and calibrated thresholds.
    """
    score = 0.02
    reasons: list[str] = []

    if tx.amount >= 100_000:
        score += 0.65
        reasons.append("very_high_amount")
    elif tx.amount >= 25_000:
        score += 0.30
        reasons.append("high_amount")

    if tx.country not in {"IN"}:
        score += 0.25
        reasons.append("cross_border_country")

    if tx.merchant_category.lower() in {"electronics", "crypto", "jewelry"}:
        score += 0.12
        reasons.append("higher_risk_merchant_category")

    score = min(round(score, 4), 1.0)
    if score >= 0.70:
        decision = "BLOCK"
    elif score >= 0.35:
        decision = "REVIEW"
    else:
        decision = "ALLOW"

    if not reasons:
        reasons.append("no_configured_risk_rules_triggered")

    return RiskAssessment(
        transaction_id=tx.transaction_id,
        risk_score=score,
        decision=decision,
        reasons=reasons,
    )
