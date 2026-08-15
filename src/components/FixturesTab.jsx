import { useState } from "react";

// Placeholder for the phase 4 build. The segmented control is real so the
// shape is visible, but neither panel has data behind it yet — deliberately
// showing nothing rather than inventing numbers.
export default function FixturesTab() {
  const [view, setView] = useState("all");

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
      ) : (
        <div className="placeholder-card">
          <h3 className="placeholder-title">Feature in progress</h3>
          <p className="placeholder-text">
            This will surface mismatched fixtures — a strong home record against a
            poor away record — so a standout tie is easy to spot.
          </p>
          <p className="placeholder-text placeholder-note">
            It will show the records themselves, never a prediction or a tip. Needs a
            form/standings data source that isn&apos;t wired up yet.
          </p>
        </div>
      )}
    </div>
  );
}
