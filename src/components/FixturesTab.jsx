import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as api from "../api/client";
import Skeleton from "./Skeleton";
import { groupAcca } from "../utils/routes";

// "2526" -> "2025/26"
function seasonLabel(code) {
  if (!code || code.length !== 4) return null;
  return `20${code.slice(0, 2)}/${code.slice(2)}`;
}

function record(side) {
  return `${side.won}W-${side.drawn}D-${side.lost}L`;
}

function kickoff(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return `${d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })} ${d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}`;
}

// Facts arranged suggestively, never a probability and never a tip. The
// mismatch is highlighted; the conclusion is left to the reader.
function MatchupCard({ m, onOpen }) {
  return (
    <button type="button" className="matchup-card" onClick={onOpen}>
      <div className="matchup-head">
        <span className="matchup-league">{m.div_name}</span>
        <span className="matchup-kickoff">{kickoff(m.commence_time)}</span>
      </div>

      <div className="matchup-sides">
        <div className={`matchup-side${m.favours === "home" ? " matchup-side-strong" : ""}`}>
          <span className="matchup-team">{m.home.team}</span>
          <span className="matchup-form">{record(m.home)} at home</span>
        </div>
        <span className="matchup-v">v</span>
        <div className={`matchup-side matchup-side-away${m.favours === "away" ? " matchup-side-strong" : ""}`}>
          <span className="matchup-team">{m.away.team}</span>
          <span className="matchup-form">{record(m.away)} away</span>
        </div>
      </div>
    </button>
  );
}

export default function FixturesTab() {
  const [view, setView] = useState("all");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showHow, setShowHow] = useState(false);
  const { groupId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    api.getFavourableMatchups()
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => { if (!cancelled) setData({ fixtures: [], error: "unavailable" }); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const season = seasonLabel(data?.season);

  return (
    <div className="fixtures-tab">
      <h2 className="section-title">Fixtures</h2>

      <div className="segmented" role="tablist" aria-label="Fixture view">
        <button
          role="tab"
          aria-selected={view === "all"}
          className={`segmented-btn${view === "all" ? " segmented-btn-active" : ""}`}
          onClick={() => setView("all")}
        >
          All
        </button>
        <button
          role="tab"
          aria-selected={view === "favourable"}
          className={`segmented-btn${view === "favourable" ? " segmented-btn-active" : ""}`}
          onClick={() => setView("favourable")}
        >
          Favourable
          <span className="beta-tag">Beta</span>
        </button>
      </div>

      {view === "all" ? (
        <div className="placeholder-card">
          <h3 className="placeholder-title">Feature in progress</h3>
          <p className="placeholder-text">
            Every fixture for the current week will be listed here, grouped by day,
            and will tap straight through to your pick.
          </p>
        </div>
      ) : loading ? (
        <div className="page-content">
          <Skeleton width="100%" height="88px" count={3} />
        </div>
      ) : (
        <div className="matchup-list">
          {season && (
            <p className="matchup-basis">
              Based on {season} home and away form.
              <button className="matchup-how" onClick={() => setShowHow((v) => !v)}>
                How this works
              </button>
            </p>
          )}

          {showHow && (
            <div className="matchup-how-panel">
              <p>
                Every club in the top four divisions plus the National League is
                ranked twice — once on home form, once on away form — as a single
                continuous ladder, so a promoted side carries its real record
                rather than an invented one.
              </p>
              <p>
                A fixture is surfaced when the gap between the home side&apos;s home
                form and the away side&apos;s away form is unusually wide. The
                division gap is measured from clubs who actually changed division,
                not assumed.
              </p>
              <p className="matchup-how-caveat">
                It highlights a mismatch. It is not a tip, it does not predict a
                result, and it takes no account of injuries, team news or
                motivation.
              </p>
            </div>
          )}

          {data?.fixtures?.length ? (
            data.fixtures.map((m) => (
              <MatchupCard key={m.event_id} m={m} onOpen={() => navigate(groupAcca(groupId))} />
            ))
          ) : (
            <div className="placeholder-card">
              <h3 className="placeholder-title">
                {data?.error ? "Not available right now" : "No strong mismatches this round"}
              </h3>
              <p className="placeholder-text">
                {data?.error
                  ? "The form data couldn't be loaded. It'll retry shortly."
                  : "Nothing stands out in the upcoming fixtures. Check back when the next round is closer."}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
