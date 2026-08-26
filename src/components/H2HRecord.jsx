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
              <p className="h2h-summary">
                All-time since 2015/16: {record.team_a} {record.summary.a_wins}W ·{" "}
                {record.summary.draws}D · {record.summary.b_wins}L, {record.summary.played} played
              </p>
              <p className="h2h-recent-heading">Recent meetings</p>
              <ul className="h2h-meetings">
                {record.meetings.map((m, i) => (
                  <li key={`${m.date}-${i}`} className="h2h-meeting">
                    {formatDate(m.date)} — {m.home} {m.home_goals}-{m.away_goals} {m.away}
                  </li>
                ))}
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
