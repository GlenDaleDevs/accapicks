import { useEffect, useState } from "react";
import * as api from "../api/client";
import Skeleton from "./Skeleton";
import "./Leagues.css";
import { FormKey, MatchRow } from "./FixtureRow";
import "./FixturesList.css";

const TRACKERS = [
  { key: "results", label: "Results" },
  { key: "btts", label: "BTTS" },
  { key: "over25", label: "Over 2.5" },
];

// "venue" shows each side its own half of the record: the home team's home
// games, the away team's away games.
const VENUES = [
  { key: "overall", label: "Overall" },
  { key: "venue", label: "Home/Away" },
];

function dayHeading(iso) {
  const d = new Date(`${iso}T12:00:00`);
  return d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" });
}

// Matches arrive in kickoff order, so a day changes at most once per pass.
function byDay(matches) {
  const days = [];
  for (const match of matches) {
    const last = days[days.length - 1];
    if (last && last.date === match.date) last.matches.push(match);
    else days.push({ date: match.date, matches: [match] });
  }
  return days;
}

export default function FixturesList({ leagueCode, onLeagues, initialWeek = "", picking = null, onTeam = null }) {
  const [week, setWeek] = useState(initialWeek);
  const [tracker, setTracker] = useState("results");
  const [venue, setVenue] = useState("overall");
  const [optionsOpen, setOptionsOpen] = useState(false);
  // Stamped with the week it came back for, so changing week shows the
  // skeleton rather than the previous week's fixtures.
  const [result, setResult] = useState(null);

  // Odds are joined server-side for one division per request, so ask for the
  // one on screen. Before the leagues list arrives the selection is always
  // the first division, so defaulting to E0 avoids a refetch when it loads.
  const fetchLeague = leagueCode || "E0";
  useEffect(() => {
    let cancelled = false;
    api.getFixtureList(week, fetchLeague)
      .then((d) => {
        if (cancelled) return;
        setResult({ week, data: d });
        onLeagues((d.leagues || []).map(({ code, name }) => ({ code, name })));
      })
      .catch(() => {
        // Keep the last known weeks list: wiping it disables both stepper
        // arrows and strands the tab on a transient failure (e.g. a 429).
        if (!cancelled) {
          setResult((prev) => ({
            week,
            data: { weeks: prev?.data?.weeks || [], leagues: [], ready: false },
          }));
        }
      });
    return () => { cancelled = true; };
  }, [week, fetchLeague, onLeagues]);

  const loading = result?.week !== week;
  const data = loading ? null : result.data;
  const leagues = data?.leagues || [];
  const league = leagues.find((l) => l.code === leagueCode) || leagues[0];
  const days = byDay(league?.matches || []);

  // Weeks run oldest first, so stepping left is back in time. The current week
  // is the first still to be played — the same one the server picks when asked
  // for none.
  // The week list survives a reload, so stepping doesn't blank the header and
  // disable the arrows while the new week is in flight.
  const weeks = (data || result?.data)?.weeks || [];
  const shownKey = week || data?.week || result?.data?.week || "";
  const index = weeks.findIndex((w) => w.key === shownKey);
  const currentKey = (weeks.find((w) => w.upcoming) || weeks[weeks.length - 1])?.key;
  const previous = index > 0 ? weeks[index - 1] : null;
  const next = index >= 0 ? weeks[index + 1] : null;
  const weekLabel = shownKey === currentKey
    ? "Current Week"
    : weeks[index]?.label || "";

  return (
    <div className="fixtures-list">
      <div className="week-nav">
        <button
          type="button"
          className="week-arrow"
          onClick={() => previous && setWeek(previous.key)}
          disabled={!previous}
          aria-label={previous ? `Previous week, ${previous.label}` : "No earlier week"}
        >
          ‹
        </button>
        <span className="week-current" aria-live="polite">{weekLabel}</span>
        <button
          type="button"
          className="week-arrow"
          onClick={() => next && setWeek(next.key)}
          disabled={!next}
          aria-label={next ? `Next week, ${next.label}` : "No later week"}
        >
          ›
        </button>
      </div>

      <div className="track">
        <button
          type="button"
          className="track-toggle"
          aria-expanded={optionsOpen}
          aria-controls="track-options"
          onClick={() => setOptionsOpen((open) => !open)}
        >
          <span>Choose what to track here</span>
          {/* The summary keeps the current choice visible while collapsed */}
          <span className="track-summary">
            {TRACKERS.find((t) => t.key === tracker)?.label}
            {" · "}
            {VENUES.find((v) => v.key === venue)?.label}
          </span>
          <span className={`track-caret${optionsOpen ? " track-caret-open" : ""}`} aria-hidden="true">›</span>
        </button>

        {optionsOpen && (
          <div className="track-options" id="track-options">
            <div className="segmented segmented-sm" role="tablist" aria-label="Bet type">
              {TRACKERS.map(({ key, label }) => (
                <button
                  key={key}
                  role="tab"
                  aria-selected={tracker === key}
                  className={`segmented-btn${tracker === key ? " segmented-btn-active" : ""}`}
                  onClick={() => setTracker(key)}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="segmented segmented-sm" role="tablist" aria-label="Home or away">
              {VENUES.map(({ key, label }) => (
                <button
                  key={key}
                  role="tab"
                  aria-selected={venue === key}
                  className={`segmented-btn${venue === key ? " segmented-btn-active" : ""}`}
                  onClick={() => setVenue(key)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="page-content">
          <Skeleton width="100%" height="44px" count={5} />
        </div>
      ) : days.length ? (
        <>
        <FormKey tracker={tracker} venue={venue} />
        {days.map((day) => (
          <section key={day.date} className="fixture-day">
            <h3 className="fixture-day-title">{dayHeading(day.date)}</h3>
            <ul className="fixture-rows">
              {day.matches.map((m) => {
                const canPick = picking ? picking.pickable(m, league) : false;
                const takenBet = picking && m.odds ? picking.takenByEvent[m.odds.id] : null;
                return (
                  <MatchRow
                    key={`${m.home}-${m.away}`}
                    match={m}
                    teams={league?.teams || {}}
                    tracker={tracker}
                    venue={venue}
                    canPick={canPick}
                    takenBy={takenBet?.username}
                    onPick={picking?.onPick}
                    submitting={picking?.submitting}
                    oddsFormat={picking?.oddsFormat}
                    onTeam={onTeam}
                  />
                );
              })}
            </ul>
          </section>
        ))}
        </>
      ) : (
        <div className="placeholder-card">
          <h3 className="placeholder-title">
            {data?.ready === false ? "Loading fixtures" : "Nothing on"}
          </h3>
          <p className="placeholder-text">
            {data?.ready === false
              ? "The fixture list is still being built. Check back in a moment."
              : "No fixtures in this league this week — try another week or league."}
          </p>
        </div>
      )}
    </div>
  );
}
