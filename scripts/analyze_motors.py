"""近畿4場のモーター機歴分析。

data/results(競走成績)と data/program(番組表)から、場ごとに現行モーターの期間を見つけ、
モーターごとに次を出す。
- ex_diff : 展示タイムのレース内中央値との差(秒)の平均。マイナスほど速い
- ex_adj  : 乗り手のクセを引いた値(その選手が他のモーターで出した展示偏差との差)の平均
- ex_top2 : 展示タイムがレース内2位以内だった割合
- ex_sd   : 展示偏差のばらつき(小さいほど安定)
- riders  : 乗った選手の人数
- fast_riders : 乗り手補正後に速かった選手の割合
- result_2r : この期間の実際の2連対率
- motor_2r  : 最新番組表の公式2連対率
隠れ上位 = ex_adj が場内上位なのに motor_2r が場内中央値以下
"""
import csv
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

VENUES = {"10": "三国", "11": "びわこ", "12": "住之江", "13": "尼崎"}
MIN_STARTS = 15


def load(dirname):
    rows = []
    for p in sorted(Path(dirname).glob("*.csv")):
        with p.open(encoding="utf-8") as f:
            rows += list(csv.DictReader(f))
    return rows


def fnum(x):
    try:
        v = float(x)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def period_start(program_rows, vc):
    """番組表のモーター2連対率の中央値がほぼ0に落ちた最後の日 = 新モーター導入日。"""
    by_day = defaultdict(list)
    for r in program_rows:
        if r["venue_code"] == vc:
            v = fnum(r["motor_2r"])
            by_day[r["date"]].append(v or 0.0)
    reset = [d for d, vals in by_day.items() if vals and st.median(vals) <= 3.0]
    return min(reset) if reset else (min(by_day) if by_day else None)  # 切替が見つからなければ番組表の最初の日から


def race_diffs(results):
    """各レースで、展示タイムのレース内中央値との差と順位を出す(4場全期間)。"""
    races = defaultdict(list)
    for r in results:
        races[(r["venue_code"], r["date"], r["race"])].append(r)
    out = []
    for (vc, d, rn), entries in races.items():
        ex = [(e, fnum(e["exhibition"])) for e in entries]
        ex = [(e, t) for e, t in ex if t]
        if len(ex) < 5:
            continue
        med = st.median(t for _, t in ex)
        for rank, (e, t) in enumerate(sorted(ex, key=lambda x: x[1]), 1):
            out.append({"vc": vc, "date": d, "race": rn, "motor": e["motor"], "racer": e["racer_number"],
                        "diff": t - med, "top2": rank <= 2, "pos": e["position"]})
    return out


def main():
    results, program = load("data/results"), load("data/program")
    diffs = race_diffs(results)
    starts = {vc: period_start(program, vc) for vc in VENUES}
    # 選手ごとの展示偏差(場・モーター別に持っておき、評価対象のモーター以外の平均を使う)
    racer_by = defaultdict(lambda: defaultdict(list))
    for d in diffs:
        racer_by[d["racer"]][(d["vc"], d["motor"], d["date"] >= (starts[d["vc"]] or ""))].append(d["diff"])
    out = {}
    for vc, name in VENUES.items():
        start = starts[vc]
        cur = [d for d in diffs if d["vc"] == vc and (start is None or d["date"] >= start)]
        races_n = len({(d["date"], d["race"]) for d in cur})
        motors = defaultdict(list)
        for d in cur:
            motors[d["motor"]].append(d)
        latest = {}
        for r in program:
            if r["venue_code"] == vc and (start is None or r["date"] >= start):
                if r["motor"] not in latest or r["date"] >= latest[r["motor"]][0]:
                    latest[r["motor"]] = (r["date"], fnum(r["motor_2r"]) or 0.0)
        table = []
        for m, ds in motors.items():
            if len(ds) < MIN_STARTS:
                continue
            adj, per_racer = [], defaultdict(list)
            for d in ds:
                other = [x for key, v in racer_by[d["racer"]].items() if key != (vc, m, True) for x in v]
                base = st.mean(other) if len(other) >= 6 else 0.0
                adj.append(d["diff"] - base)
                per_racer[d["racer"]].append(d["diff"] - base)
            sd = st.pstdev(adj)
            se = sd / len(adj) ** 0.5 if sd else 1.0
            fin = [d["pos"] for d in ds if d["pos"] not in ("", None)]
            r2 = sum(1 for p in fin if p in ("1", "2")) / len(fin) if fin else None
            table.append({"motor": int(m), "starts": len(ds), "riders": len(per_racer),
                          "ex_diff": round(st.mean(d["diff"] for d in ds), 4),
                          "ex_adj": round(st.mean(adj), 4), "t": round(st.mean(adj) / se, 2),
                          "ex_top2": round(sum(d["top2"] for d in ds) / len(ds), 3),
                          "ex_sd": round(st.pstdev(d["diff"] for d in ds), 4),
                          "fast_riders": round(sum(1 for v in per_racer.values() if st.mean(v) < 0) / len(per_racer), 3),
                          "result_2r": round(r2, 3) if r2 is not None else None,
                          "motor_2r": latest.get(m, (None, None))[1]})
        if not table:
            out[name] = {"start": start, "motors": []}
            continue
        med2r = st.median(t["motor_2r"] for t in table if t["motor_2r"] is not None)
        for t in table:
            t["hidden"] = t["t"] <= -2.0 and t["motor_2r"] is not None and t["motor_2r"] <= med2r
        out[name] = {"start": start, "races": races_n, "motor_2r_median": med2r,
                     "motors": sorted(table, key=lambda t: t["t"])}
    Path("data/analysis").mkdir(parents=True, exist_ok=True)
    Path("data/analysis/motors.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, v in out.items():
        print(f"== {name} 期間開始 {v['start']} レース数 {v.get('races')} 公式2連率中央値 {v.get('motor_2r_median')}")
        for t in v["motors"][:8]:
            print({k: t[k] for k in ("motor","starts","riders","ex_diff","ex_adj","t","ex_top2","fast_riders","result_2r","motor_2r","hidden")})


if __name__ == "__main__":
    main()
