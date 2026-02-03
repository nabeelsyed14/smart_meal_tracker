from health_score.score_logic import compute_health_score

sample = {
    "calories": 620,
    "protein": 12,
    "fat": 18
}

print("Health score:", compute_health_score(sample))
