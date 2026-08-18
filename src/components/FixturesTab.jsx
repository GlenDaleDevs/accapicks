import { useState } from "react";
import FormTab from "./FormTab";

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
          aria-selected={view === "form"}
          className={`segmented-btn${view === "form" ? " segmented-btn-active" : ""}`}
          onClick={() => setView("form")}
        >
          Form
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
        <FormTab />
      )}
    </div>
  );
}
