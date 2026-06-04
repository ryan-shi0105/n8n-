def analyze_route(old, new):

    old_routes = set(old.get("routes", []))
    new_routes = set(new.get("routes", []))

    added = new_routes - old_routes
    removed = old_routes - new_routes

    score = 0
    messages = []

    if added:
        score += len(added) * 2
        messages.append(f"Added routes: {len(added)}")

    if removed:
        score += len(removed) * 10
        messages.append(f"Removed routes: {len(removed)}")

    # route growth
    old_count = len(old_routes)
    new_count = len(new_routes)

    if old_count > 0:

        growth = ((new_count - old_count) / old_count) * 100

        if growth > 30:
            score += 20
            messages.append(f"Route growth anomaly: {growth:.1f}%")

    score = min(score, 100)

    return {
        "score": score,
        "messages": messages
    }

