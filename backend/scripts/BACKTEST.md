# Favourable Matchups — backtest findings

Run 2026-08-16. `python -m scripts.backtest_matchups` from `backend/`.

**Sample:** 2022/23 → 2025/26, E0–E3, **8,144 fixtures**, 0 unevaluated in `prior` mode.
Prices are closing odds from football-data.co.uk: `AvgC*` (market average) and `MaxC*` (best available).

**Harness trust:** home wins 43.5%, draws 25.5%, always-home ROI −5.0%, always-favourite ROI −3.6% —
all where they should be for real football with real prices. The ladder the harness builds was checked
against `build_ladders("2526")` field by field: 116 clubs, **zero mismatches**, so this measures the
model that ships, not a copy of it.

---

## Headline

**The differential is a real signal, but it is not an edge. Above the current 0.75 threshold it agrees
with the betting market 88–98% of the time — it is mostly restating the price.**

At `MIN_DIFFERENTIAL = 0.75`, over four seasons:

| | model | market favourite, same fixtures |
|---|---|---|
| bets | 1,779 | 1,779 |
| won | 54.5% | 54.9% |
| ROI at average price | **−5.1%** | −6.4% |
| ROI at best price | **−1.6%** | — |

Level with the market and losing to the margin. It should never be presented as a way to make money.

**It is genuinely useful as a "this fixture is lopsided" heuristic**, which is what the tab claims. The
win-or-draw rate climbs cleanly and monotonically with the differential, which is exactly what a
well-behaved signal looks like.

## Calibration — `prior` ladder, `adjusted` metric

| differential | bets | won | won/drew | ROI avg | ROI best | agrees w/ market |
|---|---|---|---|---|---|---|
| 0 – 0.25 | 2,332 | 41.2% | 66.2% | +2.8% | +8.3% | 54.8% |
| 0.25 – 0.5 | 2,229 | 41.0% | 69.4% | −9.6% | −5.4% | 69.3% |
| 0.5 – 0.75 | 1,666 | 47.4% | 71.3% | −3.7% | +0.2% | 78.8% |
| **0.75 – 1** | 919 | 52.2% | 75.2% | −1.8% | +2.0% | 87.6% |
| 1 – 1.25 | 533 | 52.2% | 78.4% | −11.8% | −8.7% | 95.1% |
| 1.25 – 1.5 | 215 | 59.5% | 84.2% | −5.4% | −2.1% | 95.3% |
| 1.5 – 2 | 107 | 72.9% | 88.8% | −1.0% | +1.9% | 98.1% |
| 2+ | 5 | 100% | 100% | +25.8% | +28.8% | 100% |

Win% and won/drew% both rise with the differential. ROI does not — because the market has already
priced it.

## Findings

### 1. `adjusted` is the right metric — `rank` is clearly worse
At its equivalent threshold (20 ladder places, 1,076 bets) `rank` won 46.2% for −5.6%, against the
market's 52.7% for −1.0%. Its disagreements with the market lost 17.4% over 313 bets. The shipping
default is the better of the two.

### 2. The documented "post-GW10 switch" would make things worse — do not implement it
`config.py` describes switching to the current season's ladder after gameweek 10. Measured
(`todate` mode, ladder from results so far this season), at threshold 0.75:

| matchweek | `prior` ROI | `todate` ROI |
|---|---|---|
| 1–5 | −3.2% | −4.2% |
| 6–10 | −1.1% | −1.5% |
| 11–20 | −8.7% | −20.3% |
| 21–30 | +2.5% | −2.3% |
| 31+ | −10.1% | −6.9% |

`todate` is worse or level everywhere except the closing weeks. Overall it drops from −5.1% to −8.1%.
A partial season is a noisier ladder than a complete previous one, even 30 games in — a club with two
home games sits on a 3.0 or 0.0 PPG that the model treats as fact.

`todate` also inflates differentials badly: 386 fixtures clear 2.0 versus 5 in `prior` mode, so the
same 0.75 threshold means something entirely different between the two.

### 3. The threshold is defensible, for volume rather than accuracy
ROI improves as the threshold rises (−6.5% at 0.25 → −5.1% at 0.75 → −3.5% at 1.25 → +0.2% at 1.5),
but the counts collapse: above 1.25 there are ~80 fixtures a season across four divisions, about two a
week. 0.75 yields ~445 a season, roughly **12 a week**, which is the right volume for the tab. Keep it.

### 4. 2025/26 — the season asked about — was the worst of the four

| season | bets | won | ROI |
|---|---|---|---|
| 2022/23 | 493 | 53.3% | −4.6% |
| 2023/24 | 448 | 59.8% | +2.6% |
| 2024/25 | 408 | 55.4% | −7.3% |
| **2025/26** | 430 | 49.3% | **−11.7%** |

Season-to-season swing of 14 points of ROI on ~450 bets. Any single-season read on this model is
mostly noise — which is the argument for the four-season sample.

### 5. Weakest in League Two, strongest in the Premier League
At 0.75: E0 62.1% won (−5.2%), E1 51.7% (−6.3%), E2 53.8% (−2.6%), E3 47.8% (−7.5%). League Two is
where the division offsets and promoted clubs are shakiest, and it shows.

## Anomaly worth its own look

The **0 – 0.25 bucket** — near-level fixtures, where the model is close to picking at random — returned
**+2.8% at average prices and +8.3% at best prices over 2,332 bets**. A 41.2% strike rate at a positive
return means it is systematically landing on longer-priced sides. That is either a real market
inefficiency in coin-flip fixtures or an artefact of favourite–longshot bias in how the sides get
assigned. It is the opposite of what the feature currently surfaces, and it is a bigger sample than any
above-threshold bucket. **Not acted on — it needs its own investigation before anyone believes it.**

## Recommendations (none applied)

1. **Keep `adjusted` and keep 0.75.** Both are confirmed as the better choice.
2. **Delete the post-GW10 plan.** Remove `CURRENT_SEASON` and the misleading comments from `config.py`,
   or replace them with a note pointing here. As written they describe a change that measurably hurts.
3. **Put the measured number on the card.** The tab already avoids probabilities; it could go further
   and state the backtested rate — "the favoured side has won 54% of matchups like this since 2022" —
   which is honest, specific, and more useful than an unquantified "favourable".
4. **Consider surfacing win-or-draw instead of the win.** 75% at threshold versus 52% is a far more
   dependable number, and for an acca leg the double chance is the safer pick.
5. **Investigate the 0–0.25 anomaly** before doing anything else to the model.

## Reproducing

```bash
cd backend
python scripts/backtest_matchups.py                       # full matrix
python scripts/backtest_matchups.py --seasons 2526 \
    --modes prior --metrics adjusted                      # one cut
python scripts/backtest_matchups.py --json out.json       # raw rows
```

Finished seasons are cached permanently under `PREDICTIONMODEL_CACHE_DIR`, so only the first run
downloads.
