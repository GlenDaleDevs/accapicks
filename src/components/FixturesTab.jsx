import { useState } from "react";
import FixturesList from "./FixturesList";
import FormTab from "./FormTab";
import "./Leagues.css";

const VIEWS = [
  { key: "fixtures", label: "Fixtures" },
  { key: "standings", label: "Standings" },
];

export default function FixturesTab() {
  const [view, setView] = useState("fixtures");
  // League lives here rather than in each view, so switching between fixtures
  // and the table keeps you in the league you were looking at. The list itself
  // is reported up by whichever view loaded, so the names still come from the
  // backend's division config rather than a second copy over here.
  const [leagueCode, setLeagueCode] = useState(null);
  const [leagues, setLeagues] = useState([]);

  const selected = leagues.find((l) => l.code === leagueCode) || leagues[0];
  const viewProps = {
    leagueCode: selected?.code ?? null,
    onLeagues: setLeagues,
  };

  return (
    <div className="fixtures-tab">
      <div className="league-chips" role="tablist" aria-label="League">
        {leagues.map((l) => (
          <button
            key={l.code}
            role="tab"
            aria-selected={l.code === selected?.code}
            className={`league-chip${l.code === selected?.code ? " league-chip-active" : ""}`}
            onClick={() => setLeagueCode(l.code)}
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

      {view === "fixtures" ? <FixturesList {...viewProps} /> : <FormTab {...viewProps} />}
    </div>
  );
}
