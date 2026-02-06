import { useState } from "react";
import { LEAGUE_OPTIONS, LEAGUE_NAME_MAP } from "../utils/constants";
import { formatDisplayDate } from "../utils/formatters";
import Calendar from "./Calendar";

export default function AccaWizard({ onCreated, onCancel, error }) {
  const [step, setStep] = useState(1);
  const [dates, setDates] = useState([]);
  const [leagues, setLeagues] = useState([]);
  const [name, setName] = useState("");
  const [calendarMonth, setCalendarMonth] = useState(new Date());

  const toggleDate = (dateStr) => {
    if (dates.includes(dateStr)) {
      setDates(dates.filter((d) => d !== dateStr));
    } else if (dates.length < 7) {
      setDates([...dates, dateStr]);
    }
  };

  const toggleLeague = (key) => {
    if (leagues.includes(key)) {
      setLeagues(leagues.filter((l) => l !== key));
    } else {
      setLeagues([...leagues, key]);
    }
  };

  const generateName = () => {
    const leagueNames = leagues.map((k) => LEAGUE_NAME_MAP[k] || k);
    const sorted = [...dates].sort();
    const dateDisplay = sorted
      .map((d) => {
        const dt = new Date(d + "T00:00:00");
        return dt.toLocaleDateString("en-GB", { month: "short", day: "numeric" });
      })
      .join(", ");
    return `${leagueNames.join(", ")} - ${dateDisplay}`;
  };

  const handleCreate = () => {
    const accaName = name || generateName();
    onCreated({ name: accaName, matchDates: dates, leagues, betType: "h2h" });
  };

  return (
    <div className="wizard-container">
      {/* Step indicator */}
      <div className="wizard-steps">
        {[1, 2].map((s) => (
          <div
            key={s}
            className={`wizard-step-dot ${
              step === s
                ? "wizard-step-active"
                : step > s
                  ? "wizard-step-done"
                  : "wizard-step-pending"
            }`}
          >
            {step > s ? "\u2713" : s}
          </div>
        ))}
      </div>

      {error && <div className="alert-error">{error}</div>}

      {/* Step 1: Date Selection */}
      {step === 1 && (
        <div>
          <h3 className="section-title">Select Match Dates</h3>
          <p className="section-subtitle">Choose up to 7 dates for your acca</p>
          <Calendar
            selectedDates={dates}
            maxDates={7}
            currentMonth={calendarMonth}
            onToggleDate={toggleDate}
            onMonthChange={setCalendarMonth}
          />
          <div className="btn-group mt-16">
            <button className="btn btn-ghost" onClick={onCancel}>
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={() => setStep(2)}
              disabled={dates.length === 0}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Step 2: League Selection + Name + Confirm */}
      {step === 2 && (
        <div>
          <h3 className="section-title">Select Leagues</h3>
          <p className="section-subtitle">Choose which leagues to include (1-5)</p>
          <div className="mb-16">
            {LEAGUE_OPTIONS.map((league) => (
              <label
                key={league.key}
                className={`league-option${leagues.includes(league.key) ? " league-option-selected" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={leagues.includes(league.key)}
                  onChange={() => toggleLeague(league.key)}
                  disabled={leagues.length >= 5 && !leagues.includes(league.key)}
                />
                <span className="league-option-name">{league.name}</span>
              </label>
            ))}
          </div>
          <div className="form-group">
            <label className="form-label">Acca Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={generateName()}
              maxLength={100}
            />
          </div>
          <div className="wizard-summary">
            <p className="section-subtitle">
              {leagues.length} league{leagues.length !== 1 ? "s" : ""}, {dates.length} date{dates.length !== 1 ? "s" : ""}
            </p>
          </div>
          <div className="btn-group">
            <button className="btn btn-ghost" onClick={() => setStep(1)}>
              Back
            </button>
            <button
              className="btn btn-success"
              onClick={handleCreate}
              disabled={leagues.length === 0 || leagues.length > 5}
            >
              Create Acca
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
