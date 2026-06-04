import os
import json
import re

from collections import defaultdict

from vlan_diff import analyze_vlan
from route_diff import analyze_route
from config_diff import analyze_config
from scoring import calculate_total_score


# =====================================================
# CONFIG
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(BASE_DIR, "output")

REPORT_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# =====================================================
# LOAD JSON
# =====================================================

def load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================
# GET DEVICE JSON PAIRS
# =====================================================


def get_device_json_pairs(output_dir):

    device_groups = defaultdict(list)

    # -------------------------------------------------
    # find json files
    # -------------------------------------------------

    files = [
        f for f in os.listdir(output_dir)
        if f.endswith(".json")
    ]

    print("\n========== JSON FILES ==========")

    for x in files:
        print(x)

    # -------------------------------------------------
    # group by device
    # -------------------------------------------------

    for file in files:

        """
        example:

        BQ_xxx_20251228-0103-57_ok.json
        HQ_xxx_20260329-0113-02_ok.json
        """

        # remove timestamp + suffix
        device = re.sub(
            r"_\d{8}-\d{4}-\d{2}.*\.json",
            "",
            file
        )

        full_path = os.path.join(
            output_dir,
            file
        )

        device_groups[device].append(full_path)

    # -------------------------------------------------
    # debug print
    # -------------------------------------------------

    print("\n========== DEVICE GROUPS ==========")

    for device, file_list in device_groups.items():

        print(f"\n{device}")

        for f in file_list:
            print(f"   {f}")

    # -------------------------------------------------
    # pair old/new
    # -------------------------------------------------

    pairs = {}

    for device, file_list in device_groups.items():

        if len(file_list) < 2:

            print(f"\n⚠ {device} JSON 不足兩份，跳過")

            continue

        # sort by filename
        sorted_files = sorted(file_list)

        old_file = sorted_files[-2]
        new_file = sorted_files[-1]

        pairs[device] = (
            old_file,
            new_file
        )

        print("\n------------------------------------")
        print(f"PAIR SUCCESS: {device}")

        print(f"OLD:")
        print(old_file)

        print(f"NEW:")
        print(new_file)

    return pairs


# =====================================================
# ANALYZE
# =====================================================

def analyze(old_file, new_file):

    old = load_json(old_file)
    new = load_json(new_file)

    results = {}

    # VLAN
    vlan_result = analyze_vlan(old, new)
    results["vlan"] = vlan_result

    # ROUTE
    route_result = analyze_route(old, new)
    results["route"] = route_result

    # CONFIG
    config_result = analyze_config(old, new)
    results["config"] = config_result

    # TOTAL SCORE
    total_score = calculate_total_score(results)

    results["total_score"] = total_score

    return results


# =====================================================
# PRINT REPORT
# =====================================================

def print_report(device, results):

    print("\n====================================")
    print(f"DEVICE: {device}")
    print("====================================")

    for category, result in results.items():

        if category == "total_score":
            continue

        print(f"\n[{category.upper()}]")
        print(f"score: {result['score']}")

        if result["messages"]:

            for msg in result["messages"]:
                print(f" - {msg}")

        else:
            print(" - No significant changes")

    print("\n------------------------------------")

    print(f"TOTAL SCORE = {results['total_score']}")

    if results["total_score"] >= 70:

        print("STATUS = LIKELY ISSUE")

    elif results["total_score"] >= 40:

        print("STATUS = POTENTIAL ISSUE")

    else:

        print("STATUS = NORMAL")

    print("------------------------------------\n")


# =====================================================
# SAVE REPORT
# =====================================================

def save_report(device, results):

    report_file = os.path.join(
        REPORT_DIR,
        f"{device}_report.json"
    )

    with open(report_file, "w", encoding="utf-8") as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"✅ Report saved:")
    print(report_file)


# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":

    try:

        pairs = get_device_json_pairs(OUTPUT_DIR)

        if not pairs:

            print("\n❌ 沒有足夠 JSON 可分析")
            exit()

        # -------------------------------------------------
        # analyze each device
        # -------------------------------------------------

        for device, (old_file, new_file) in pairs.items():

            print("\n====================================")
            print(f"DEVICE: {device}")

            print(f"OLD FILE:")
            print(old_file)

            print(f"NEW FILE:")
            print(new_file)

            results = analyze(
                old_file,
                new_file
            )

            print_report(
                device,
                results
            )

            save_report(
                device,
                results
            )

    except Exception as e:

        print(f"\n❌ ERROR: {e}")
