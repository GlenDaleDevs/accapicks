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

export default function FixturesList({ leagueCode, onLeagues }) {
  const [week, setWeek] = useState("");
  const [tracker, setTracker] = useState("results");
  const [venue, setVenue] = useState("overall");
  // Stamped with the week it came back for, so changing week shows the
  // skeleton rather than the previous week's fixtures.
  const [result, setResult] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api.getFixtureList(week)
      .then((d) => {
        if (cancelled) return;
        setResult({ week, data: d });
        onLeagues((d.leagues || []).map(({ code, name }) => ({ code, name })));
      })
      .catch(() => { if (!cancelled) setResult({ week, data: { weeks: [], leagues: [], ready: false } }); });
    return () => { cancelled = true; };
  }, [week, onLeagues]);

  const loading = result?.week !== week;
  const data = loading ? null : result.data;
  const leagues = data?.leagues || [];
  const league = leagues.find((l) => l.code === leagueCode) || leagues[0];
  const days = byDay(league?.matches || []);

  return (
    <div className="fixtures-list">
      <div className="league-controls">
        <select
          className="league-select"
          // The server picks the week when we ask for none, so reflect its
          // answer back into the picker rather than showing a blank option.
          value={week || data?.week || ""}
          onChange={(e) => setWeek(e.target.value)}
          aria-label="Week"
        >
          {(data?.weeks || []).map((w) => (
            <option key={w.key} value={w.key}>
              {w.label}{w.upcoming ? "" : " (results)"}
            </option>
          ))}
        </select>

        <span className="control-label" id="tracker-label">Choose what to track</span>
        <div
          className="segmented segmented-sm"
          role="tablist"
          aria-labelledby="tracker-label"
        >
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
              {day.matches.map((m) => (
                <MatchRow
                  key={`${m.home}-${m.away}`}
                  match={m}
                  teams={league?.teams || {}}
                  tracker={tracker}
                  venue={venue}
                />
              ))}
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
              : "No fixtures for this league that week — an international break, most likely."}
          </p>
        </div>
      )}
    </div>
  );
}
