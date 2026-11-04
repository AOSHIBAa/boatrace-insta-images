"""BOAT RACE公式の競走成績(LZH)から近畿4場の出走データをCSVに貯める。

使い方: python scripts/fetch_results.py [開始日 YYYY-MM-DD] [終了日 YYYY-MM-DD]
省略時は「CSVがまだない日」を昨日まで(最大120日前まで)さかのぼって取得する。
"""
import csv
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from boatrace_lzh import LzhDownloader, PerformanceParser

VENUES = {"10": "三国", "11": "びわこ", "12": "住之江", "13": "尼崎"}
OUT = Path("data/results")
FIELDS = ["date", "venue_code", "venue", "race", "boat", "racer_number", "racer_name",
          "motor", "boat_part", "exhibition", "entrance", "st", "position", "race_time",
          "wind_dir", "wind_speed", "wave", "weather"]


def days(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main():
    yesterday = date.today() - timedelta(days=1)
    if len(sys.argv) >= 3:
        start, end = date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])
    else:
        start, end = yesterday - timedelta(days=120), yesterday
    OUT.mkdir(parents=True, exist_ok=True)
    dl = LzhDownloader(cache_dir=".cache", max_workers=1)
    parser = PerformanceParser()
    for d in days(start, end):
        out = OUT / f"{d.isoformat()}.csv"
        if out.exists():
            continue
        try:
            files = dl.download(d, "performance")
        except Exception as e:  # 開催なし・未公開など
            print(f"{d}: skip ({e})")
            continue
        if not files:
            print(f"{d}: no file")
            continue
        res = parser.parse(files)
        names = {r.racer_number: getattr(r, "name", "") for r in res.racers} if res.racers else {}
        races = {(r.venue_code, r.race_number): r for r in res.races}
        rows = []
        for e in res.entries:
            if e.venue_code not in VENUES:
                continue
            r = races.get((e.venue_code, e.race_number))
            rows.append({
                "date": d.isoformat(), "venue_code": e.venue_code, "venue": VENUES[e.venue_code],
                "race": e.race_number, "boat": e.boat_number, "racer_number": e.racer_number,
                "racer_name": names.get(e.racer_number, ""), "motor": e.motor_number,
                "boat_part": e.boat_part, "exhibition": e.exhibition_time,
                "entrance": e.entrance_position, "st": e.st_timing, "position": e.result_position,
                "race_time": e.result_time,
                "wind_dir": getattr(r, "wind_direction", None), "wind_speed": getattr(r, "wind_speed", None),
                "wave": getattr(r, "wave_height", None), "weather": getattr(r, "weather", None),
            })
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(f"{d}: {len(rows)} rows")
        time.sleep(2)  # 配信サーバーに負荷をかけない


if __name__ == "__main__":
    main()
