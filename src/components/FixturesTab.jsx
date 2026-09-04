import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import FixturesList from "./FixturesList";
import FormTab from "./FormTab";
import * as api from "../api/client";
import useCurrentAcca from "../hooks/useCurrentAcca";
import { useApp } from "../context/AppContext";
import { showToast } from "../utils/toast";
import { buildPick, buildStructuredData } from "../utils/pickDescription";
import { groupAcca, groupTeam } from "../utils/routes";
import "./Leagues.css";

const VIEWS = [
  { key: "fixtures", label: "Fixtures" },
  { key: "standings", label: "Standings" },
];

// The date that opens a date's game week — mirrors fixturelist._week_start
// EXACTLY, so "land on the acca's week" agrees with the server's bucketing.
// Weekend (Fri–Mon) and midweek (Tue–Thu) get separate keys. getDay() is
// Sun=0..Sat=6, so convert to Python's Mon=0..Sun=6 first, then use the same map.
function weekKeyFor(dateIso) {
  const d = new Date(`${dateIso}T12:00:00`);
  const wd = (d.getDay() + 6) % 7; // Mon=0 .. Sun=6
  const back = wd === 0 ? 3 : wd >= 4 ? wd - 4 : wd - 1;
  d.setDate(d.getDate() - back);
  return d.toISOString().slice(0, 10);
}

export default function FixturesTab() {
  const { groupId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user, oddsFormat } = useApp();
  const acca = useCurrentAcca(groupId);

  const [view, setView] = useState("fixtures");
  // League lives here rather than in each view, so switching between fixtures
  // and the table keeps you in the league you were looking at. The list itself
  // is reported up by whichever view loaded, so the names still come from the
  // backend's division config rather than a second copy over here. Seeded from
  // (and written back to) the URL so tapping a team and pressing back returns
  // to the league you were on, not the default.
  const [leagueCode, setLeagueCode] = useState(() => searchParams.get("league"));

  // Keep the URL in step with the selected league (replace, so flicking through
  // leagues doesn't stack history entries), so browser-back restores it.
  const selectLeague = (code) => {
    setLeagueCode(code);
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("league", code);
        return next;
      },
      { replace: true },
    );
  };
  const [leagues, setLeagues] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  // Arriving from "Add your pick" preselects the acca's week. Consumed once,
  // then cleared, so back-navigation or a refresh doesn't re-select it.
  const [initialWeek] = useState(() =>
    location.state?.week ? weekKeyFor(location.state.week) : ""
  );
  useEffect(() => {
    if (location.state?.week) navigate(location.pathname, { replace: true });
  }, [location, navigate]);

  const takenByEvent = useMemo(() => {
    const taken = {};
    for (const bet of acca?.bets || []) {
      if (bet.event_id) taken[bet.event_id] = bet;
    }
    return taken;
  }, [acca]);

  // Every term here closes a dead end: getAccaState only applies the lock
  // check when everyone has picked, and a never-picked acca has a null
  // locks_at, so it sits "open" long after its kickoffs.
  const pickable = useCallback(
    (match, league) => {
      if (!acca || acca.status !== "open" || !user) return false;
      if (acca.locks_at && new Date(acca.locks_at) <= new Date()) return false;
      if (match.played || !match.odds || !match.kickoff) return false;
      if (new Date(match.kickoff) <= new Date()) return false;
      if ((acca.bets || []).some((b) => b.user_id === user.id)) return false;
      if (takenByEvent[match.odds.id]) return false;
      if (!acca.match_dates?.includes(match.date)) return false;
      if (!acca.leagues?.includes(league?.odds_key)) return false;
      return true;
    },
    [acca, user, takenByEvent]
  );

  const onPick = useCallback(
    async (match, pickType) => {
      if (submitting || !acca) return;
      const built = buildPick(match, pickType);
      if (!built) return;
      setSubmitting(true);
      try {
        await api.createBet(acca.id, built.description, built.odds, buildStructuredData(match, pickType));
        showToast("Pick added", "success");
        navigate(groupAcca(groupId));
      } catch (err) {
        showToast(err.response?.data?.detail || "Failed to add pick", "error");
        setSubmitting(false);
      }
    },
    [submitting, acca, navigate, groupId]
  );

  const selected = leagues.find((l) => l.code === leagueCode) || leagues[0];
  const viewProps = {
    leagueCode: selected?.code ?? null,
    onLeagues: setLeagues,
  };
  const picking = { pickable, takenByEvent, onPick, submitting, oddsFormat };

  // Division isn't in scope where a team name renders (FixturesList only
  // knows the league's odds_key), so build the nav handler up here where
  // groupId and the selected league code both live.
  const onTeam = selected?.code
    ? (name) => navigate(groupTeam(groupId, selected.code, name))
    : null;

  return (
    <div className="fixtures-tab">
      <div className="league-chips" role="tablist" aria-label="League">
        {leagues.map((l) => (
          <button
            key={l.code}
            role="tab"
            aria-selected={l.code === selected?.code}
            className={`league-chip${l.code === selected?.code ? " league-chip-active" : ""}`}
            onClick={() => selectLeague(l.code)}
          >
            {l.name}
          </button>
        ))}
      </div>

      <div className="segmented" role="tablist" aria-label="View">
        {VIEWS.map(({ key, label }) => (
          <button
            key={key}
            role="tab"
            aria-selected={view === key}
            className={`segmented-btn${view === key ? " segmented-btn-active" : ""}`}
            onClick={() => setView(key)}
          >
            {label}
          </button>
        ))}
      </div>

      {view === "fixtures" ? (
        <FixturesList {...viewProps} initialWeek={initialWeek} picking={picking} onTeam={onTeam} />
      ) : (
        <FormTab {...viewProps} />
      )}
    </div>
  );
}
