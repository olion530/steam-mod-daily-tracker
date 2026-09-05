#!/usr/bin/env python3
from __future__ import annotations

# Daily Steam Workshop snapshot collector for the seven tracked STS2 mods.
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
LATEST_JSON = DATA_DIR / "latest.json"
LATEST_MD = DATA_DIR / "latest.md"

STEAM_ENDPOINT = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
TZ = ZoneInfo("Asia/Shanghai")

MODS = [
    {"id": "3795933082", "name": "Yoink! — Speed Picks"},
    {"id": "3795496818", "name": "Always Fight Two Bosses at Any Ascension"},
    {"id": "3795496596", "name": "Relic Rewards: Choose One of Three"},
    {"id": "3786269745", "name": "ORBSSSSSSS！！！！"},
    {"id": "3778713629", "name": "Prismatic Gem"},
    {"id": "3772547670", "name": "德纳修斯大帝 / Sire Denathrius"},
    {"id": "3752747984", "name": "OUCHMOD"},
]

STEAM_FIELDS = {
    "views": "views",
    "subscriptions": "subscriptions",
    "favorites": "favorited",
    "comments": "num_comments_public",
}


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def fetch_details() -> dict:
    form = {"itemcount": str(len(MODS))}
    for i, mod in enumerate(MODS):
        form[f"publishedfileids[{i}]"] = mod["id"]

    body = urllib.parse.urlencode(form).encode("utf-8")
    req = urllib.request.Request(
        STEAM_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "sts2-mod-daily-tracker/1.0",
        },
    )

    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Steam request failed after 3 attempts: {last_error}")


def load_previous(today: str) -> dict | None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    candidates = sorted(p for p in HISTORY_DIR.glob("*.json") if p.stem < today)
    if not candidates:
        return None
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


def fmt(value):
    return "—" if value is None else f"{value:,}"


def fmt_delta(value):
    if value is None:
        return "—"
    if value > 0:
        return f"+{value:,}"
    return f"{value:,}"


def main():
    now = datetime.now(TZ)
    today = now.strftime("%Y-%m-%d")
    raw = fetch_details()

    raw_items = raw.get("response", {}).get("publishedfiledetails", [])
    by_id = {str(item.get("publishedfileid")): item for item in raw_items}

    previous = load_previous(today)
    prev_by_id = {
        str(row["id"]): row for row in (previous or {}).get("mods", [])
    }

    rows = []
    for mod in MODS:
        wid = mod["id"]
        item = by_id.get(wid, {})
        ok = to_int(item.get("result")) == 1

        row = {
            "id": wid,
            "name": mod["name"],
            "workshop_url": f"https://steamcommunity.com/sharedfiles/filedetails/?id={wid}",
            "steam_result": to_int(item.get("result")),
        }
        for out_key, steam_key in STEAM_FIELDS.items():
            row[out_key] = to_int(item.get(steam_key)) if ok else None

        old = prev_by_id.get(wid)
        delta = {}
        for key in STEAM_FIELDS:
            current_value = row.get(key)
            old_value = old.get(key) if old else None
            if isinstance(current_value, int) and isinstance(old_value, int):
                delta[key] = current_value - old_value
            else:
                delta[key] = None
        row["delta"] = delta
        rows.append(row)

    snapshot = {
        "date": today,
        "generated_at": now.isoformat(),
        "timezone": "Asia/Shanghai",
        "source": STEAM_ENDPOINT,
        "mods": rows,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    (HISTORY_DIR / f"{today}.json").write_text(text, encoding="utf-8")
    LATEST_JSON.write_text(text, encoding="utf-8")

    lines = [
        f"# STS2 MOD 日报 — {today}",
        "",
        f"采集时间：{now.strftime('%Y-%m-%d %H:%M:%S')}（Asia/Shanghai）",
        "",
        "| MOD | 浏览量 | 较昨日 | 订阅量 | 较昨日 | 收藏量 | 较昨日 | 留言 | 较昨日 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        d = row["delta"]
        lines.append(
            f"| {row['name']} | {fmt(row['views'])} | {fmt_delta(d['views'])} | "
            f"{fmt(row['subscriptions'])} | {fmt_delta(d['subscriptions'])} | "
            f"{fmt(row['favorites'])} | {fmt_delta(d['favorites'])} | "
            f"{fmt(row['comments'])} | {fmt_delta(d['comments'])} |"
        )
    lines.append("")
    LATEST_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
