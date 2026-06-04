import os
import re
import json
import sqlite3

from datetime import datetime
from collections import defaultdict


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_DIR = os.path.join(BASE_DIR, "raw_logs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

DB_FILE = os.path.join(BASE_DIR, "devices.db")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


VOLATILITY_KEYS = [
    "show processes cpu",
    "show proc cpu",
    "show fabric utilization",
    "show buffer"
]

TREND_KEYS = [
    "show flash",
    "show bootflash",
    "show platform hardware capacity fabric"
]

STATIC_KEYS = [
    "show running-config",
    "show version",
    "show ip int brief",
    "show vlan brief",
    "show int status",
    "show ip route"
]

TOPOLOGY_KEYS = [
    "show ip eigrp neighbors",
    "show ip eigrp topology",
    "show ip bgp neighbors",
    "show ip ospf neighbor",
    "show cdp neighbors"
]


NORMALIZE_MAP = {

    # running
    "sh run": "show running-config",
    "show run": "show running-config",

    # version
    "sh ver": "show version",

    # interface
    "sh ip int brief": "show ip int brief",
    "sh int status": "show int status",

    # vlan
    "sh vlan brief": "show vlan brief",

    # route
    "sh ip route": "show ip route",

    # topology
    "sh cdp nei": "show cdp neighbors",
    "sh ip ospf nei": "show ip ospf neighbor",
    "sh ip bgp nei": "show ip bgp neighbors",
    "sh ip eigrp nei": "show ip eigrp neighbors",
}

ALL_KEYS = (
    VOLATILITY_KEYS +
    TREND_KEYS +
    STATIC_KEYS +
    TOPOLOGY_KEYS
)

# SQLITE
def init_db():

    conn = sqlite3.connect(DB_FILE)

    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT,
            file_name TEXT,
            processed_time TEXT,
            PRIMARY KEY(device_id, file_name)
        )
    """)

    conn.commit()

    return conn

def normalize_command(line):

    line = line.lower().strip()

    # remove hostname prompt
    line = re.sub(r"^.*?#", "", line)

    # normalize spaces
    line = re.sub(r"\s+", " ", line)

    for short_cmd, full_cmd in NORMALIZE_MAP.items():

        if line.startswith(short_cmd):
            return full_cmd

    return line

def get_category(cmd):

    if cmd in VOLATILITY_KEYS:
        return "volatility"

    if cmd in TREND_KEYS:
        return "trend"

    if cmd in STATIC_KEYS:
        return "static"

    if cmd in TOPOLOGY_KEYS:
        return "topology"

    return None


def parse_log(file_path):

    parsed = defaultdict(list)

    current_cmd = None
    current_output = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:

        for raw_line in f:

            line = raw_line.rstrip("\n")

            normalized = normalize_command(line)

            matched = next(
                (k for k in ALL_KEYS if normalized.startswith(k)),
                None
            )

            if matched:

                # save previous block
                if current_cmd:

                    category = get_category(current_cmd)

                    if category:

                        parsed[category].append({
                            "command": current_cmd,
                            "output": current_output
                        })

                current_cmd = matched
                current_output = []

            else:

                if current_cmd:
                    current_output.append(line)


    if current_cmd:

        category = get_category(current_cmd)

        if category:

            parsed[category].append({
                "command": current_cmd,
                "output": current_output
            })

    return parsed

def export_json(original_file, parsed_data):


    json_name = original_file.replace(".log", ".json")

    output_file = os.path.join(
        OUTPUT_DIR,
        json_name
    )

    with open(output_file, "w", encoding="utf-8") as f:

        json.dump(
            parsed_data,
            f,
            indent=2,
            ensure_ascii=False
        )

    return output_file


def process_all_logs():

    conn = init_db()

    files = [
        f for f in os.listdir(RAW_DIR)
        if f.lower().endswith(".log")
    ]

    if not files:

        print("No log files found")

        return

    print("\n========== FOUND LOG FILES ==========")

    for f in files:
        print(f)


    for file in files:

        file_path = os.path.join(RAW_DIR, file)

        print(f"\n========== PROCESSING ==========")
        print(file)

        device_name = re.sub(
            r"_\d{8}-\d{2}-\d{2}.*",
            "",
            file
        )

        print(f"DEVICE: {device_name}")

        parsed = parse_log(file_path)

        output_file = export_json(
            file,
            parsed
        )

        print(f"JSON exported:")
        print(output_file)

        total_cmds = 0

        for category, items in parsed.items():

            print(f"  {category}: {len(items)} commands")

            total_cmds += len(items)

        print(f"  total: {total_cmds} commands")

      # sqlite
      
        c = conn.cursor()

        c.execute("""
            INSERT OR REPLACE INTO devices
            VALUES (?, ?, ?)
        """, (
            device_name,
            file,
            datetime.now().isoformat()
        ))

        conn.commit()

    conn.close()

    print("\n===================================")
    print("ALL LOGS PROCESSED")
    print("===================================")

if __name__ == "__main__":

    process_all_logs()
