def assess_risk(features):
    score = 0

    if features["new_receiver"]:
        score += 2

    if features["new_device"]:
        score += 2

    if features["large_amount"]:
        score += 2

    if features["international_transfer"]:
        score += 1

    if features["late_night"]:
        score += 2

    if features["many_login_attempts"]:
        score += 2

    if features["rapid_transfer"]:
        score += 1

    if features["high_risk_payment_rail"]:
        score += 1

    if score <= 2:
        risk = "LOW"
        action = "APPROVE"
    elif score <= 5:
        risk = "MEDIUM"
        action = "REVIEW"
    else:
        risk = "HIGH"
        action = "BLOCK"

    return risk, action, score