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

export default function FixturesList() {
  const [week, setWeek] = useState("");
  const [leagueCode, setLeagueCode] = useState(null);
  const [tracker, setTracker] = useState("results");
  // Stamped with the week it came back for, so changing week shows the
  // skeleton rather than the previous week's fixtures.
  const [result, setResult] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api.getFixtureList(week)
      .then((d) => { if (!cancelled) setResult({ week, data: d }); })
      .catch(() => { if (!cancelled) setResult({ week, data: { weeks: [], leagues: [], ready: false } }); });
    return () => { cancelled = true; };
  }, [week]);

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

        <div className="segmented segmented-sm" role="tablist" aria-label="Tracker">
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
      </div>

      <div className="league-chips" role="tablist" aria-label="League">
        {leagues.map((l) => (
          <button
            key={l.code}
            role="tab"
            aria-selected={l.code === league?.code}
            className={`league-chip${l.code === league?.code ? " league-chip-active" : ""}`}
            onClick={() => setLeagueCode(l.code)}
          >
            {l.name}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="page-content">
          <Skeleton width="100%" height="44px" count={5} />
        </div>
      ) : days.length ? (
        <>
        <FormKey tracker={tracker} />
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
