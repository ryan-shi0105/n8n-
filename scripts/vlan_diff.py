def analyze_vlan(old, new):

    old_vlans = set(old.get("vlans", []))
    new_vlans = set(new.get("vlans", []))

    added = new_vlans - old_vlans
    removed = old_vlans - new_vlans

    score = 0
    messages = []

    if added:
        score += len(added) * 5
        messages.append(f"Added VLANs: {sorted(list(added))}")

    if removed:
        score += len(removed) * 15
        messages.append(f"Removed VLANs: {sorted(list(removed))}")

    score = min(score, 100)

    return {
        "score": score,
        "messages": messages
    }
