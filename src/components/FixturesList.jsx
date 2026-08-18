import { useEffect, useState } from "react";
import * as api from "../api/client";
import Skeleton from "./Skeleton";
import "./Leagues.css";
import "./FixturesList.css";

function dayHeading(iso) {
  const d = new Date(`${iso}T12:00:00`);
  return d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" });
}

function kickoffTime(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
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

const OUTCOME_TITLE = { W: "Won", D: "Drew", L: "Lost" };

// Oldest to newest, so the rightmost circle is the most recent result.
function Form({ form }) {
  if (!form?.length) return null;
  return (
    <span className="fixture-form">
      {form.map((outcome, i) => (
        <span
          key={i}
          className={`form-dot form-${outcome.toLowerCase()}`}
          title={OUTCOME_TITLE[outcome]}
        />
      ))}
      <span className="sr-only">Form: {form.join(", ")}</span>
    </span>
  );
}

function Team({ name, stats }) {
  return (
    <div className="fixture-team">
      {stats?.pos ? <span className="fixture-pos">{stats.pos}</span> : null}
      <span className="fixture-name">{name}</span>
      <Form form={stats?.form} />
    </div>
  );
}

function MatchRow({ match, teams }) {
  return (
    <li className="fixture-row">
      <Team name={match.home} stats={teams[match.home]} />
      <span className={`fixture-mid${match.played ? " fixture-score" : ""}`}>
        {match.played ? `${match.home_goals}–${match.away_goals}` : kickoffTime(match.kickoff)}
      </span>
      <Team name={match.away} stats={teams[match.away]} />
    </li>
  );
}

// Dots alone don't say which end is the latest game, and nobody should have to
// guess from the data.
function FormKey() {
  return (
    <p className="fixture-key">
      <span className="fixture-key-item"><span className="form-dot form-w" />Won</span>
      <span className="fixture-key-item"><span className="form-dot form-d" />Drew</span>
      <span className="fixture-key-item"><span className="form-dot form-l" />Lost</span>
      <span className="fixture-key-note">Last 5, most recent on the right</span>
    </p>
  );
}

export default function FixturesList() {
  const [week, setWeek] = useState("");
  const [leagueCode, setLeagueCode] = useState(null);
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
        <FormKey />
        {days.map((day) => (
          <section key={day.date} className="fixture-day">
            <h3 className="fixture-day-title">{dayHeading(day.date)}</h3>
            <ul className="fixture-rows">
              {day.matches.map((m) => (
                <MatchRow key={`${m.home}-${m.away}`} match={m} teams={league?.teams || {}} />
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
