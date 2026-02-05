import { useState } from "react";
import { LEAGUE_OPTIONS, LEAGUE_NAME_MAP } from "../utils/constants";
import { formatDisplayDate } from "../utils/formatters";
import Calendar from "./Calendar";

export default function AccaWizard({ onCreated, onCancel, error }) {
  const [step, setStep] = useState(1);
  const [dates, setDates] = useState([]);
  const [leagues, setLeagues] = useState([]);
  const [betType, setBetType] = useState("h2h");
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
    onCreated({ name: accaName, matchDates: dates, leagues, betType });
  };

  return (
    <div className="wizard-container">
      {/* Step indicator */}
      <div className="wizard-steps">
        {[1, 2, 3, 4].map((s) => (
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

      {/* Step 2: League Selection */}
      {step === 2 && (
        <div>
          <h3 className="section-title">Select Leagues</h3>
          <p className="section-subtitle">Choose which leagues to include</p>
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
                />
                <span className="league-option-name">{league.name}</span>
              </label>
            ))}
          </div>
          <p className="section-subtitle">
            Selected: {leagues.length} league{leagues.length !== 1 ? "s" : ""}
          </p>
          <div className="btn-group">
            <button className="btn btn-ghost" onClick={() => setStep(1)}>
              Back
            </button>
            <button
              className="btn btn-primary"
              onClick={() => setStep(3)}
              disabled={leagues.length === 0}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Bet Type Selection */}
      {step === 3 && (
        <div>
          <h3 className="section-title">Select Bet Type</h3>
          <div className="mb-16">
            <label className="bettype-option bettype-option-active">
              <input
                type="radio"
                name="betType"
                value="h2h"
                checked={betType === "h2h"}
                onChange={() => setBetType("h2h")}
              />
              <div>
                <strong className="bettype-title">Win / Draw / Lose Only</strong>
                <p className="bettype-desc">
                  Pick a team to win or a draw for each match
                </p>
              </div>
            </label>
            <label className="bettype-option bettype-option-disabled">
              <input type="radio" name="betType" value="all" disabled />
              <div>
                <strong className="bettype-title-disabled">
                  All Bet Types (Coming Soon)
                </strong>
                <p className="bettype-desc-disabled">
                  Over/under, both teams to score, correct score, etc.
                </p>
              </div>
            </label>
          </div>
          <div className="btn-group">
            <button className="btn btn-ghost" onClick={() => setStep(2)}>
              Back
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                setName(generateName());
                setStep(4);
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Name & Summary */}
      {step === 4 && (
        <div>
          <h3 className="section-title">Name Your Acca</h3>
          <div className="form-group">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Acca name"
            />
          </div>
          <div className="wizard-summary">
            <h4>Summary</h4>
            <p>
              <strong>Dates:</strong>{" "}
              {[...dates].sort().map((d) => formatDisplayDate(d)).join(", ")}
            </p>
            <p>
              <strong>Leagues:</strong>{" "}
              {leagues.map((k) => LEAGUE_NAME_MAP[k]).join(", ")}
            </p>
            <p>
              <strong>Bet Type:</strong> Win / Draw / Lose
            </p>
          </div>
          <div className="btn-group">
            <button className="btn btn-ghost" onClick={onCancel}>
              Cancel
            </button>
            <button className="btn btn-success" onClick={handleCreate}>
              Create & Add Picks
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
