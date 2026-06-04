import hashlib


def md5(text):

    return hashlib.md5(text.encode()).hexdigest()


def analyze_config(old, new):

    old_cfg = old.get("running_config", "")
    new_cfg = new.get("running_config", "")

    score = 0
    messages = []

    if md5(old_cfg) != md5(new_cfg):

        old_lines = set(old_cfg.splitlines())
        new_lines = set(new_cfg.splitlines())

        added = new_lines - old_lines
        removed = old_lines - new_lines

        score += min(len(added) + len(removed), 50)

        messages.append(f"Config changed")
        messages.append(f"Added lines: {len(added)}")
        messages.append(f"Removed lines: {len(removed)}")

    return {
        "score": score,
        "messages": messages
    }

