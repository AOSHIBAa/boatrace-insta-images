"""BOAT RACE公式の番組表(LZH)から、近畿4場のモーター・ボートの2連対率をCSVに貯める。
使い方: python scripts/fetch_program.py [開始日] [終了日]
"""
import csv
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from boatrace_lzh import LzhDownloader

VENUES = {"10": "三国", "11": "びわこ", "12": "住之江", "13": "尼崎"}
OUT = Path("data/program")
ROW = re.compile(r"^([1-6]) (\d{4})(.+?)(\d{2})(\D{2,3}?)(\d{2})([AB][12]) +([\d.]+) +([\d.]+) +([\d.]+) +([\d.]+) +(\d+) +([\d.]+) +(\d+) +([\d.]+)")
RACE = re.compile(r"^\s*([０-９\d]{1,2})Ｒ")
Z2H = str.maketrans("０１２３４５６７８９", "0123456789")
FIELDS = ["date", "venue_code", "venue", "race", "boat", "racer_number", "racer_name", "racer_class",
          "nat_win", "nat_2r", "loc_win", "loc_2r", "motor", "motor_2r", "boat_part", "boat_2r"]


def parse(text, d):
    rows, venue, race = [], None, None
    for line in text.splitlines():
        m = re.match(r"^(\d{2})BBGN", line)
        if m:
            venue, race = m.group(1), None
            continue
        if re.match(r"^\d{2}BEND", line):
            venue = None
            continue
        if venue not in VENUES:
            continue
        r = RACE.match(line)
        if r:
            race = int(r.group(1).translate(Z2H))
            continue
        e = ROW.match(line)
        if e and race:
            g = e.groups()
            rows.append({"date": d.isoformat(), "venue_code": venue, "venue": VENUES[venue], "race": race,
                         "boat": int(g[0]), "racer_number": int(g[1]), "racer_name": g[2].replace("　", ""),
                         "racer_class": g[6], "nat_win": g[7], "nat_2r": g[8], "loc_win": g[9], "loc_2r": g[10],
                         "motor": int(g[11]), "motor_2r": g[12], "boat_part": int(g[13]), "boat_2r": g[14]})
    return rows


def main():
    today = date.today()
    if len(sys.argv) >= 3:
        start, end = date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])
    else:
        start, end = today - timedelta(days=120), today
    OUT.mkdir(parents=True, exist_ok=True)
    dl = LzhDownloader(cache_dir=".cache", max_workers=1, timeout=20)
    d = start
    while d <= end:
        out = OUT / f"{d.isoformat()}.csv"
        if not out.exists() or d >= today - timedelta(days=1):
            try:
                files = dl.download(d, "schedule")
            except Exception as ex:
                files = None
                print(f"{d}: skip ({ex})", flush=True)
            if files:
                rows = []
                for text in files.values():
                    rows += parse(text, d)
                with out.open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=FIELDS)
                    w.writeheader()
                    w.writerows(rows)
                print(f"{d}: {len(rows)} rows", flush=True)
            time.sleep(2)
        d += timedelta(days=1)


if __name__ == "__main__":
    main()
