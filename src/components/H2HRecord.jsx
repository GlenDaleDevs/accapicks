import { useRef, useState } from "react";
import { getH2H } from "../api/client";

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "2-digit" });
}

// Head-to-head record, tucked behind a lazy tap — same pattern as MoreBets
// in FixtureOdds.jsx: fetch once on first open, cache in state, toggle an
// inline panel on every tap after that. Meaningful on any fixture, not just
// ones still open to pick, so this isn't gated on canPick.
export function H2HRecord({ home, away }) {
  const [open, setOpen] = useState(false);
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(false);
  const fetchingRef = useRef(false);

  const toggle = async () => {
    const willOpen = !open;
    setOpen(willOpen);
    if (willOpen && !record && !fetchingRef.current) {
      fetchingRef.current = true;
      setLoading(true);
      try {
        setRecord(await getH2H(home, away));
      } catch {
        // Leave record null — panel falls back to the "couldn't load" note
      } finally {
        fetchingRef.current = false;
        setLoading(false);
      }
    }
  };

  return (
    <>
      <button type="button" className="h2h-toggle" aria-expanded={open} onClick={toggle}>
        {open ? "Hide H2H Record" : "H2H Record"}
      </button>
      {open && (
        <div className="h2h-panel">
          {loading && <span className="h2h-note">Loading head-to-head…</span>}
          {!loading && record && !record.ready && (
            <span className="h2h-note">Still loading, try again in a moment</span>
          )}
          {!loading && record && record.ready && record.summary.played === 0 && (
            <span className="h2h-note">No previous meetings in our records.</span>
          )}
          {!loading && record && record.ready && record.summary.played > 0 && (
            <>
              {/* Tally: a number per outcome with the team it belongs to named
                  underneath, so it reads at a glance instead of "3W · 1D · 2L". */}
              <div className="h2h-tally">
                <div className="h2h-tally-col">
                  <span className="h2h-tally-num h2h-num-a">{record.summary.a_wins}</span>
                  <span className="h2h-tally-label">{record.team_a}</span>
                </div>
                <div className="h2h-tally-col">
                  <span className="h2h-tally-num h2h-num-d">{record.summary.draws}</span>
                  <span className="h2h-tally-label">{record.summary.draws === 1 ? "Draw" : "Draws"}</span>
                </div>
                <div className="h2h-tally-col">
                  <span className="h2h-tally-num h2h-num-b">{record.summary.b_wins}</span>
                  <span className="h2h-tally-label">{record.team_b}</span>
                </div>
              </div>
              <div className="h2h-bar" aria-hidden="true">
                {record.summary.a_wins > 0 && (
                  <span className="h2h-bar-seg h2h-seg-a" style={{ flexGrow: record.summary.a_wins }} />
                )}
                {record.summary.draws > 0 && (
                  <span className="h2h-bar-seg h2h-seg-d" style={{ flexGrow: record.summary.draws }} />
                )}
                {record.summary.b_wins > 0 && (
                  <span className="h2h-bar-seg h2h-seg-b" style={{ flexGrow: record.summary.b_wins }} />
                )}
              </div>
              <p className="h2h-caption">
                {record.summary.played} {record.summary.played === 1 ? "meeting" : "meetings"} since 2015/16
              </p>
              <p className="h2h-recent-heading">Recent meetings</p>
              <ul className="h2h-meetings">
                {record.meetings.slice(0, 8).map((m, i) => {
                  const homeWon = m.home_goals > m.away_goals;
                  const awayWon = m.away_goals > m.home_goals;
                  return (
                    <li key={`${m.date}-${i}`} className="h2h-meeting">
                      <span className={`h2h-side h2h-side-home${homeWon ? " h2h-side-win" : ""}`}>{m.home}</span>
                      <span className="h2h-meeting-score">{m.home_goals}–{m.away_goals}</span>
                      <span className={`h2h-side h2h-side-away${awayWon ? " h2h-side-win" : ""}`}>{m.away}</span>
                      <span className="h2h-meeting-date">{formatDate(m.date)}</span>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
          {!loading && !record && (
            <span className="h2h-note">Couldn't load head-to-head right now.</span>
          )}
        </div>
      )}
    </>
  );
}
