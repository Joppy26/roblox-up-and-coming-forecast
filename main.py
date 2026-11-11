#!/usr/bin/env python3
"""Predict Roblox's Up-and-Coming top 10 (make.fun bounty roblox-up-and-coming-forecast-01).

Reads /input/history.ndjson (chart reads, oldest first) and /input/task.json,
writes /output/forecast.json: one probability per (game, place 1..10) plus a
top-10 ordering. Python 3.13, standard library only, no network, deterministic.

Model: a two-component mixture over each game's rank history.
  * Narrow component (weight ALPHA): the last read's chart, smeared with a
    narrow Gaussian (SIGMA_NARROW). The window's first hours sit close to the
    last read, so the last chart deserves a sharp vote.
  * Wide component (weight 1-ALPHA): every read, time-decayed with time
    constant TAU_HOURS and smeared with a wide Gaussian (SIGMA_WIDE). This is
    the diffused rank distribution of the later window hours, once the fast
    chart has had time to move.
Each place keeps (1 - UNNAMED) of its mass; the UNNAMED share is left for
games that enter the chart during the window and so cannot be named.

Tuned by backtest on the public archive (46 reads, 2026-10-30 to 2026-11-11):
9 sliding 72-hour holdouts, log score (higher is better, 0 is best):
  this model   avg -38.73, worst -43.05
  persistence  avg -46.57, worst -53.12
  rank trend   avg -54.28, worst -59.78
Practice window (train 34 reads, score 10 reads): this model -35.46 vs the
house persistence baseline -43.51. The model beat persistence on all 9
holdouts. Rank velocity, game age and Top Trending membership were all tested
and dropped: each made the backtest worse.
"""

import json
import math
import os
from datetime import datetime, timezone

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# Mixture weights and kernel widths, from the backtest above.
ALPHA = 0.85            # weight on the last read's narrow kernel
SIGMA_NARROW = 3.0      # ranks: narrow kernel width (last read)
TAU_HOURS = 6.0         # recency decay for the wide component
SIGMA_WIDE = 10.0       # ranks: wide kernel width (history)
UNNAMED = 0.25          # per-place share left unnamed (future entrants)
MAX_ROWS_PER_PLACE = 100
MIN_P = 0.0001          # the scorer floors probabilities here anyway


def parse_time(value):
    """ISO 8601 UTC timestamp -> aware datetime, or None."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def load_reads(input_dir):
    """Return [(datetime, [(rank, universe_id), ...]), ...] oldest first."""
    path = os.path.join(input_dir, "history.ndjson")
    reads = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            at = parse_time(row.get("at"))
            chart = row.get("up_and_coming")
            if at is None or not isinstance(chart, list):
                continue
            games = []
            for game in chart:
                if not isinstance(game, dict):
                    continue
                rank = game.get("rank")
                uid = game.get("universe_id")
                if isinstance(rank, int) and isinstance(uid, int):
                    games.append((rank, uid))
            if games:
                games.sort()
                reads.append((at, games))
    reads.sort(key=lambda item: item[0])
    return reads


def forecast(reads, places):
    """Build the forecast dict from the read history."""
    if not reads:
        return {"probabilities": [], "top10": list(range(1, places + 1))}
    t_last = reads[-1][0]
    # scores[(universe_id, place)] = unnormalised mass
    scores = {}

    def add(uid, place, mass):
        if mass <= 0.0:
            return
        key = (uid, place)
        scores[key] = scores.get(key, 0.0) + mass

    # Narrow component: the last read only.
    for rank, uid in reads[-1][1]:
        for place in range(1, places + 1):
            d = rank - place
            kv = math.exp(-(d * d) / (2.0 * SIGMA_NARROW * SIGMA_NARROW))
            if kv > 1e-4:
                add(uid, place, ALPHA * kv)

    # Wide component: every read, time-decayed.
    for at, games in reads:
        age_h = (t_last - at).total_seconds() / 3600.0
        w = (1.0 - ALPHA) * math.exp(-age_h / TAU_HOURS)
        if w < 0.005:
            continue
        for rank, uid in games:
            for place in range(1, places + 1):
                d = rank - place
                kv = math.exp(-(d * d) / (2.0 * SIGMA_WIDE * SIGMA_WIDE))
                if kv > 1e-4:
                    add(uid, place, w * kv)

    probabilities = []
    total_mass = {}
    for place in range(1, places + 1):
        cand = [(s, uid) for (uid, p), s in scores.items() if p == place]
        cand.sort(key=lambda item: (-item[0], item[1]))
        tot = sum(s for s, _ in cand)
        if tot <= 0.0:
            continue
        for s, uid in cand[:MAX_ROWS_PER_PLACE]:
            p = (1.0 - UNNAMED) * s / tot
            if p < MIN_P:
                continue
            probabilities.append({"universe_id": uid, "place": place, "p": p})
            total_mass[uid] = total_mass.get(uid, 0.0) + p

    top10 = [uid for uid, _ in
             sorted(total_mass.items(), key=lambda item: (-item[1], item[0]))[:places]]
    if len(top10) < places:
        for _, uid in reads[-1][1]:
            if uid not in top10:
                top10.append(uid)
            if len(top10) == places:
                break
    return {"probabilities": probabilities, "top10": top10}


def main():
    task_path = os.path.join(INPUT_DIR, "task.json")
    with open(task_path, "r", encoding="utf-8") as fh:
        task = json.load(fh)
    places = int(task.get("places", 10))
    output_name = task.get("output", "forecast.json")
    reads = load_reads(INPUT_DIR)
    result = forecast(reads, places)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, output_name)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    main()
