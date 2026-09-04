// A club's season so far: league position, record, form and results —
// reached by tapping a team name on the Fixtures tab. All data comes from
// the free football-data.co.uk results the Fixtures/Form tabs already use,
// so this costs no odds-API credits.
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as api from "../api/client";
import { Form } from "./FormDots";
import Skeleton from "./Skeleton";
import "./Leagues.css";
import "./TeamDetail.css";

const SPLITS = [
  { key: "overall", label: "Overall" },
  { key: "home", label: "Home" },
  { key: "away", label: "Away" },
];

function resultClass(result) {
  if (result === "W") return "team-result-w";
  if (result === "L") return "team-result-l";
  return "team-result-d";
}

export default function TeamDetail() {
  const { division, name } = useParams();
  const navigate = useNavigate();
  const teamName = decodeURIComponent(name);

  const [season, setSeason] = useState("current");
  const [split, setSplit] = useState("overall");
  // Stamped with the season it came back for, so switching season shows the
  // skeleton rather than the previous season's page until the fetch lands.
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api.getTeamDetail(division, teamName, season)
      .then((d) => {
        if (cancelled) return;
        setError("");
        setResult({ season, data: d });
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.response?.data?.detail || "Failed to load team");
      });
    return () => { cancelled = true; };
  }, [division, teamName, season]);

  const loading = !error && result?.season !== season;
  const data = loading ? null : result?.data;
  const table = data?.table;
  const fixtures = data?.fixtures || [];
  const formSplit = data?.form?.[split];
  const move = data?.move;
  const shownDivisionName = data?.shown_division_name;

  return (
    <div className="page-content team-detail">
      <button className="btn btn-ghost mb-20" onClick={() => navigate(-1)}>
        &larr; Back
      </button>

      {error ? (
        <div className="alert-error">{error}</div>
      ) : loading ? (
        <>
          <Skeleton width="200px" height="24px" count={1} />
          <div className="skeleton-spacer">
            <Skeleton width="100%" height="80px" count={2} />
          </div>
        </>
      ) : (
        <>
          <h2 className="section-title">{teamName}</h2>

          {move ? (
            <div className={`team-move-badge team-move-badge-${move}`}>
              {move === "relegated" ? "Relegated from" : "Promoted from"} {shownDivisionName}
            </div>
          ) : null}

          <div className="team-header">
            {table ? (
              <>
                <div className="team-pos-badge">{table.pos ?? "–"}</div>
                <div className="team-record">
                  <span className="team-record-line">
                    P{table.played} W{table.won} D{table.drawn} L{table.lost}
                  </span>
                  <span className="team-record-line team-record-muted">
                    GF{table.gf} GA{table.ga} GD{table.gd > 0 ? `+${table.gd}` : table.gd}
                  </span>
                </div>
                <div className="team-points">
                  <span className="team-points-value">{table.points}</span>
                  <span className="team-points-label">Pts</span>
                </div>
              </>
            ) : (
              <p className="placeholder-text team-no-table">
                No table position for {season === "current" ? "this season" : "last season"} yet.
              </p>
            )}
          </div>

          <div className="league-controls team-controls">
            <select
              className="league-select"
              value={season}
              onChange={(e) => setSeason(e.target.value)}
              aria-label="Season"
            >
              <option value="current">This season</option>
              <option value="last">Last season</option>
            </select>

            <div className="segmented segmented-sm" role="tablist" aria-label="Form split">
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

          <div className="team-form-row">
            <span className="team-form-label">Results</span>
            <Form marks={formSplit?.results} tracker="results" emptyLabel="No games played yet" />
          </div>
          <div className="team-form-row">
            <span className="team-form-label">BTTS</span>
            <Form marks={formSplit?.btts} tracker="btts" emptyLabel="No games played yet" />
          </div>
          <div className="team-form-row">
            <span className="team-form-label">Over 2.5</span>
            <Form marks={formSplit?.over25} tracker="over25" emptyLabel="No games played yet" />
          </div>

          {fixtures.length === 0 ? (
            <div className="placeholder-card">
              <h3 className="placeholder-title">
                {season === "current" ? "No games played yet this season" : "No results for last season"}
              </h3>
              <p className="placeholder-text">
                {season === "current"
                  ? "It's early days — try last season to see how this club got on."
                  : "This club may not have data from that season, or the name doesn't match a played fixture."}
              </p>
            </div>
          ) : (
            <ul className="team-results">
              {fixtures.map((f) => (
                <li key={`${f.date}-${f.opponent}`} className="team-result-row">
                  <span className="team-result-date">
                    {new Date(`${f.date}T12:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
                  </span>
                  <span className="team-result-venue">{f.venue === "home" ? "H" : "A"}</span>
                  <span className="team-result-opponent">{f.opponent}</span>
                  <span className={`team-result-score ${resultClass(f.result)}`}>
                    {f.gf}–{f.ga}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
