"""BOAT RACE公式の競走成績(LZH)から、近畿4場の払戻金をCSVに貯める。
使い方: python scripts/fetch_payouts.py [開始日] [終了日]
"""
import csv
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from boatrace_lzh import LzhDownloader, PerformanceParser

VENUES = {"10": "三国", "11": "びわこ", "12": "住之江", "13": "尼崎"}
OUT = Path("data/payouts")


def main():
    yesterday = date.today() - timedelta(days=1)
    if len(sys.argv) >= 3:
        start, end = date.fromisoformat(sys.argv[1]), date.fromisoformat(sys.argv[2])
    else:
        start, end = yesterday - timedelta(days=7), yesterday
    OUT.mkdir(parents=True, exist_ok=True)
    dl = LzhDownloader(cache_dir=".cache", max_workers=1, timeout=20)
    parser = PerformanceParser()
    d = start
    while d <= end:
        out = OUT / f"{d.isoformat()}.csv"
        if not out.exists():
            files = None
            try:
                files = dl.download(d, "performance")
            except Exception as e:
                print(f"{d}: skip ({e})", flush=True)
            if files:
                res = parser.parse(files)
                rows = []
                for p in res.payouts:
                    if p.venue_code in VENUES:
                        row = {k: getattr(p, k, None) for k in ("venue_code", "race_number", "ticket_type", "winning_combination", "payout", "popularity")}
                        row["date"] = d.isoformat()
                        row["venue"] = VENUES[p.venue_code]
                        rows.append(row)
                with out.open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=["date", "venue_code", "venue", "race_number", "ticket_type", "winning_combination", "payout", "popularity"])
                    w.writeheader()
                    w.writerows(rows)
                print(f"{d}: {len(rows)} rows", flush=True)
            time.sleep(2)
        d += timedelta(days=1)


if __name__ == "__main__":
    main()
