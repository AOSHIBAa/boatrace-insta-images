"""指定モーターが舟券にどう絡んだか(穴での貢献)を集計する。
使い方: python scripts/analyze_payouts.py 場名:番号 [場名:番号 ...]
"""
import csv
import glob
import sys
import json
import statistics as st
from collections import defaultdict

VENUE_CODE = {"三国": "10", "びわこ": "11", "住之江": "12", "尼崎": "13"}
an = json.load(open("data/analysis/motors.json", encoding="utf-8"))

res = []
for p in sorted(glob.glob("data/results/*.csv")):
    res += list(csv.DictReader(open(p, encoding="utf-8")))
pay = defaultdict(dict)  # (vc,date,race) -> {ticket: [(comb, payout, pop)]}
for p in sorted(glob.glob("data/payouts/*.csv")):
    for r in csv.DictReader(open(p, encoding="utf-8")):
        k = (r["venue_code"], r["date"], r["race_number"])
        pay[k].setdefault(r["ticket_type"], []).append((r["winning_combination"], int(r["payout"] or 0), r["popularity"]))
pay_dates = {k[1] for k in pay}
end = max(pay_dates) if pay_dates else None


def stats(vc, motor, start):
    rows = [r for r in res if r["venue_code"] == vc and r["motor"] == str(motor) and r["date"] >= start and r["date"] in pay_dates]
    n = len(rows)
    win = place = top3 = 0
    tan = fuku = 0
    hits = []
    for r in rows:
        k = (vc, r["date"], r["race"])
        b = r["boat"]
        pos = r["position"]
        pp = pay.get(k, {})
        if pos == "1":
            win += 1
            tan += sum(x[1] for x in pp.get("tansho", []) if x[0] == b)
        if pos in ("1", "2"):
            place += 1
            fuku += sum(x[1] for x in pp.get("fukusho", []) if x[0] == b)
        if pos in ("1", "2", "3"):
            top3 += 1
            for comb, yen, pop in pp.get("sanrensho", []):
                hits.append({"date": r["date"], "race": r["race"], "boat": b, "pos": pos, "comb": comb, "yen": yen,
                             "pop": int(pop) if pop and pop.isdigit() else None, "name": r["racer_name"], "entrance": r["entrance"]})
    return {"starts": n, "win": win, "top2": place, "top3": top3, "tansho_roi": round(tan / n, 1) if n else None,
            "fukusho_roi": round(fuku / n, 1) if n else None, "hits": hits}


def venue_base(vc, start):
    rows = [r for r in res if r["venue_code"] == vc and r["date"] >= start and r["date"] in pay_dates]
    tan = fuku = 0
    for r in rows:
        pp = pay.get((vc, r["date"], r["race"]), {})
        if r["position"] == "1":
            tan += sum(x[1] for x in pp.get("tansho", []) if x[0] == r["boat"])
        if r["position"] in ("1", "2"):
            fuku += sum(x[1] for x in pp.get("fukusho", []) if x[0] == r["boat"])
    san = [x[1] for k, v in pay.items() if k[0] == vc and k[1] >= start for x in v.get("sanrensho", [])]
    return {"tansho_roi": round(tan / len(rows), 1), "fukusho_roi": round(fuku / len(rows), 1),
            "sanrentan_median": st.median(san) if san else None, "manshu_rate": round(sum(1 for x in san if x >= 10000) / len(san), 3) if san else None}


out = {"end": end, "motors": {}, "base": {}}
for arg in sys.argv[1:]:
    venue, m = arg.split(":")
    vc = VENUE_CODE[venue]
    start = max(an[venue]["start"], min(pay_dates))
    if venue not in out["base"]:
        out["base"][venue] = venue_base(vc, start) | {"start": start}
    s = stats(vc, int(m), start)
    yens = [h["yen"] for h in s["hits"]]
    s["sanrentan_median"] = st.median(yens) if yens else None
    s["manshu"] = sum(1 for y in yens if y >= 10000)
    s["top_hits"] = sorted(s["hits"], key=lambda h: -h["yen"])[:5]
    del s["hits"]
    out["motors"][arg] = s
print(json.dumps(out, ensure_ascii=False, indent=1))
