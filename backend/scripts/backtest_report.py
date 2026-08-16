"""Aggregation and printing for the Favourable Matchups backtest.

Every cut is reported against price. A hit rate on its own is worthless — 70%
on odds-on favourites still loses money — so each row carries the return on a
1-unit stake at the market average and at the best available price.
"""

INF = float("inf")

BUCKETS = {
    "adjusted": [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, INF],
    # Ladder places, so a different scale entirely.
    "rank": [0, 5, 10, 20, 30, 45, 60, INF],
}

SWEEPS = {
    "adjusted": [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
    "rank": [5, 10, 20, 30, 45, 60],
}

ROUND_BANDS = [(1, 5), (6, 10), (11, 20), (21, 30), (31, 99)]


def price(row, side, best=False):
    if side == "home":
        return row["max_h"] if best else row["avg_h"]
    if side == "away":
        return row["max_a"] if best else row["avg_a"]
    return None


def settle(rows, side_of, best=False):
    """(bets, hit %, ROI %) for a strategy that backs `side_of(row)` each time."""
    staked = 0
    won = 0
    profit = 0.0
    for row in rows:
        side = side_of(row)
        if not side:
            continue
        odds = price(row, side, best=best)
        if not odds:
            continue
        staked += 1
        if row["outcome"] == side:
            won += 1
            profit += odds - 1
        else:
            profit -= 1
    if not staked:
        return 0, None, None
    return staked, 100 * won / staked, 100 * profit / staked


def win_or_draw(rows, side_of):
    """Hit % if a draw also counted. No price — double chance isn't in the CSVs."""
    n = hit = 0
    for row in rows:
        side = side_of(row)
        if not side:
            continue
        n += 1
        if row["outcome"] in (side, "draw"):
            hit += 1
    return (100 * hit / n) if n else None


MODEL = lambda row: row["favours"]  # noqa: E731
HOME = lambda row: "home"  # noqa: E731


def market(row):
    if not row["avg_h"] or not row["avg_a"]:
        return None
    return "home" if row["avg_h"] < row["avg_a"] else "away"


def _fmt(value, suffix="%"):
    return "—" if value is None else f"{value:+.1f}{suffix}" if suffix == "%" and abs(value) < 100 else f"{value:.1f}{suffix}"


def _pct(value):
    return "—" if value is None else f"{value:.1f}%"


def _roi(value):
    return "—" if value is None else f"{value:+.1f}%"


def _table(title, headers, rows):
    print(f"\n{title}")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def sanity(rows):
    """The checks that decide whether anything else here can be believed."""
    total = len(rows)
    home_wins = sum(1 for r in rows if r["outcome"] == "home")
    draws = sum(1 for r in rows if r["outcome"] == "draw")
    n, hit, roi = settle(rows, HOME)
    mn, mhit, mroi = settle(rows, market)
    print(f"\nFixtures evaluated       {total}")
    print(f"Home wins                {100 * home_wins / total:.1f}%   (expect ~44%)")
    print(f"Draws                    {100 * draws / total:.1f}%   (expect ~25%)")
    print(f"Always-home ROI          {_roi(roi)}   over {n} priced fixtures (expect a few % negative)")
    print(f"Always-favourite ROI     {_roi(mroi)}   hit {_pct(mhit)} over {mn}")


def by_bucket(rows, metric):
    edges = BUCKETS[metric]
    out = []
    for low, high in zip(edges, edges[1:]):
        band = [r for r in rows if low <= abs(r["differential"]) < high]
        if not band:
            continue
        n, hit, roi = settle(band, MODEL)
        _, _, roi_max = settle(band, MODEL, best=True)
        agree = sum(1 for r in band if market(r) and market(r) == r["favours"])
        label = f"{low:g} – {high:g}" if high != INF else f"{low:g}+"
        out.append([
            label, n, _pct(hit), _pct(win_or_draw(band, MODEL)),
            _roi(roi), _roi(roi_max),
            _pct(100 * agree / len(band)),
        ])
    _table(
        "By differential bucket",
        ["differential", "bets", "won", "won/drew", "ROI avg", "ROI best", "agrees w/ market"],
        out,
    )


def sweep(rows, metric):
    out = []
    for threshold in SWEEPS[metric]:
        band = [r for r in rows if abs(r["differential"]) >= threshold]
        if not band:
            continue
        n, hit, roi = settle(band, MODEL)
        _, _, roi_max = settle(band, MODEL, best=True)
        # The only question that matters: does the model beat simply backing
        # the shorter price on the same fixtures?
        _, mhit, mroi = settle(band, market)
        out.append([
            f">= {threshold:g}", n, _pct(hit), _roi(roi), _roi(roi_max),
            _pct(mhit), _roi(mroi),
        ])
    _table(
        "Threshold sweep — model vs backing the market favourite on the same fixtures",
        ["threshold", "bets", "model won", "model ROI", "model ROI best",
         "market won", "market ROI"],
        out,
    )


def disagreements(rows, metric, threshold):
    """Where the model and the market pick different sides. If the model has an
    edge at all, it has to show up here."""
    band = [r for r in rows if abs(r["differential"]) >= threshold and market(r)]
    against = [r for r in band if market(r) != r["favours"]]
    if not against:
        print(f"\nModel never disagrees with the market above {threshold:g}.")
        return
    n, hit, roi = settle(against, MODEL)
    _, mhit, mroi = settle(against, market)
    print(f"\nWhere the model disagrees with the market (|diff| >= {threshold:g})")
    print(f"  {len(against)} of {len(band)} fixtures ({100 * len(against) / len(band):.1f}%)")
    print(f"  backing the model's side:  won {_pct(hit)}, ROI {_roi(roi)} over {n}")
    print(f"  backing the market's side: won {_pct(mhit)}, ROI {_roi(mroi)}")


def by_round(rows, metric, threshold):
    band = [r for r in rows if abs(r["differential"]) >= threshold]
    out = []
    for low, high in ROUND_BANDS:
        sub = [r for r in band if low <= r["round"] <= high]
        if not sub:
            continue
        n, hit, roi = settle(sub, MODEL)
        out.append([f"{low}–{high if high < 99 else '+'}", n, _pct(hit), _roi(roi)])
    _table(f"By matchweek (|diff| >= {threshold:g})",
           ["rounds", "bets", "won", "ROI avg"], out)


def by_division(rows, metric, threshold):
    band = [r for r in rows if abs(r["differential"]) >= threshold]
    out = []
    for code in ("E0", "E1", "E2", "E3"):
        sub = [r for r in band if r["div"] == code]
        if not sub:
            continue
        n, hit, roi = settle(sub, MODEL)
        out.append([code, n, _pct(hit), _roi(roi)])
    _table(f"By division (|diff| >= {threshold:g})",
           ["div", "bets", "won", "ROI avg"], out)


def by_season(rows, metric, threshold, seasons):
    band = [r for r in rows if abs(r["differential"]) >= threshold]
    out = []
    for season in seasons:
        sub = [r for r in band if r["season"] == season]
        if not sub:
            continue
        n, hit, roi = settle(sub, MODEL)
        out.append([season, n, _pct(hit), _roi(roi)])
    _table(f"By season (|diff| >= {threshold:g}) — is the result stable?",
           ["season", "bets", "won", "ROI avg"], out)


DEFAULT_THRESHOLD = {"adjusted": 0.75, "rank": 20}


def print_report(everything, seasons):
    for (mode, metric), (rows, skipped) in everything.items():
        threshold = DEFAULT_THRESHOLD[metric]
        print("\n" + "=" * 78)
        print(f"  mode={mode}  metric={metric}   ({skipped} fixtures unevaluated)")
        print("=" * 78)
        if not rows:
            print("no fixtures evaluated")
            continue
        sanity(rows)
        by_bucket(rows, metric)
        sweep(rows, metric)
        disagreements(rows, metric, threshold)
        by_round(rows, metric, threshold)
        by_division(rows, metric, threshold)
        by_season(rows, metric, threshold, seasons)
