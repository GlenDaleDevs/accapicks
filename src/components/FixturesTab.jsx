import { useState } from "react";
import FixturesList from "./FixturesList";
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

      {view === "all" ? <FixturesList /> : <FormTab />}
    </div>
  );
}
