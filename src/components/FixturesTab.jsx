import { useState } from "react";
import FixturesList from "./FixturesList";
import FormTab from "./FormTab";

const VIEWS = [
  { key: "fixtures", label: "Fixtures" },
  { key: "standings", label: "Standings" },
];

export default function FixturesTab() {
  const [view, setView] = useState("fixtures");
  // Held here rather than in each view, so switching between fixtures and the
  // table keeps you in the league you were looking at.
  const [leagueCode, setLeagueCode] = useState(null);

  return (
    <div className="fixtures-tab">
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
        <FixturesList leagueCode={leagueCode} onLeagueChange={setLeagueCode} />
      ) : (
        <FormTab leagueCode={leagueCode} onLeagueChange={setLeagueCode} />
      )}
    </div>
  );
}
