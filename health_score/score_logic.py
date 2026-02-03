def compute_health_score(nutrition):
    score = 100

    calories = nutrition["calories"]
    protein = nutrition["protein"]
    fat = nutrition["fat"]

    # Portion awareness
    if calories > 700:
        score -= 25
    elif calories > 500:
        score -= 10

    # Protein adequacy
    if protein < 10:
        score -= 15

    # Fat moderation
    if fat > 25:
        score -= 10

    return max(score, 0)
