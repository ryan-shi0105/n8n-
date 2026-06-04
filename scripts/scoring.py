id="a5"
def calculate_total_score(results):

    total = 0

    weights = {
        "config": 1.3,
        "route": 1.5,
        "vlan": 1.4,
        "interface": 1.2
    }

    for category, result in results.items():

        if category not in weights:
            continue

        score = result.get("score", 0)

        total += score * weights[category]

    return int(min(total, 100))

