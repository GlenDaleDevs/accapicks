import { useEffect, useState } from "react";
import * as api from "../api/client";
import Skeleton from "./Skeleton";
import StandingsTable from "./StandingsTable";
import "./Leagues.css";
import "./Standings.css";

// "2526" -> "2025/26"
function seasonLabel(code) {
  if (!code || code.length !== 4) return null;
  return `20${code.slice(0, 2)}/${code.slice(2)}`;
}

const SPLITS = [
  { key: "overall", label: "Overall" },
  { key: "home", label: "Home" },
  { key: "away", label: "Away" },
];

export default function FormTab() {
  const [season, setSeason] = useState("current");
  const [split, setSplit] = useState("overall");
  const [leagueCode, setLeagueCode] = useState(null);
  // Stamped with the season it came back for, so switching season shows the
  // skeleton rather than the previous season's table until the fetch lands.
  const [result, setResult] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api.getStandings(season)
      .then((d) => { if (!cancelled) setResult({ season, data: d }); })
      .catch(() => { if (!cancelled) setResult({ season, data: { leagues: [], ready: false } }); });
    return () => { cancelled = true; };
  }, [season]);

  const loading = result?.season !== season;
  const data = loading ? null : result.data;
  const leagues = data?.leagues || [];
  // Fall back to the first league so a code that only exists in one season
  // can't leave the view blank.
  const league = leagues.find((l) => l.code === leagueCode) || leagues[0];
  const rows = league?.[split] || [];

  return (
    <div className="standings">
      <div className="league-controls">
        <select
          className="league-select"
          value={season}
          onChange={(e) => setSeason(e.target.value)}
          aria-label="Season"
        >
          <option value="current">This season</option>
          <option value="last">Last season</option>
        </select>

        <div className="segmented segmented-sm" role="tablist" aria-label="Table split">
          {SPLITS.map(({ key, label }) => (
            <button
              key={key}
              role="tab"
              aria-selected={split === key}
              className={`segmented-btn${split === key ? " segmented-btn-active" : ""}`}
              onClick={() => setSplit(key)}
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
          <Skeleton width="100%" height="44px" count={6} />
        </div>
      ) : rows.length ? (
        <>
          <StandingsTable rows={rows} />
          <p className="standings-basis">
            {seasonLabel(data?.season)} {split === "overall" ? "table" : `${split} table`} —
            results from football-data.co.uk
          </p>
        </>
      ) : (
        <div className="placeholder-card">
          <h3 className="placeholder-title">
            {data?.ready === false ? "Loading tables" : "No matches played yet"}
          </h3>
          <p className="placeholder-text">
            {data?.ready === false
              ? "The tables are still being built. Check back in a moment."
              : "This season hasn't started for this division. Switch to last season to see the final table."}
          </p>
        </div>
      )}
    </div>
  );
}
