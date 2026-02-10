import { useState } from "react";
import { BOOKMAKER_DISPLAY_NAMES, LEAGUE_NAME_MAP } from "../utils/constants";
import { formatOdds, formatBetSlipText, formatDisplayDate, formatKickoffTime } from "../utils/formatters";
import * as api from "../api/client";

export default function BetSlip({ acca, oddsFormat, bookmakerComparison, bookmakerLinks = {}, onRemovePick, user }) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  if (!acca) return null;

  const isSettled = ["settled", "won", "lost"].includes(acca.status);

  if (acca.bets.length === 0) {
    if (acca.status === "locked" || isSettled) {
      return (
        <div className="bet-slip">
          <div className="bet-slip-perforation" />
          <div className="bet-slip-inner">
            <div className="bet-slip-header">
              <div className="bet-slip-header-title">ACCUMULATOR BET SLIP</div>
            </div>
            <p className="bet-slip-empty">NO PICKS SUBMITTED</p>
          </div>
        </div>
      );
    }
    return null;
  }

  // Find best bookmaker from comparison data
  let bestBookmaker = null;
  let bestBookmakerUrl = null;
  let bestBookmakerKey = null;

  if (bookmakerComparison && typeof bookmakerComparison === "object") {
    const entries = Object.entries(bookmakerComparison)
      .filter(([, d]) => d && typeof d.total_odds === "number")
      .sort((a, b) => b[1].total_odds - a[1].total_odds);

    if (entries.length > 0) {
      bestBookmakerKey = entries[0][0];
      bestBookmaker = bookmakerLinks[bestBookmakerKey]?.display_name || BOOKMAKER_DISPLAY_NAMES[bestBookmakerKey] || bestBookmakerKey;
      bestBookmakerUrl = bookmakerLinks[bestBookmakerKey]?.url;
    }
  }

  const combinedOdds = acca.bets.reduce((acc, bet) => acc * parseFloat(bet.odds), 1);

  const handleCopy = async () => {
    setError("");
    const text = formatBetSlipText(acca, oddsFormat, bestBookmaker);

    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      try {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
        setCopied(true);
      } catch {
        setCopied(false);
        setError("Failed to copy to clipboard");
        return;
      }
    }
    setTimeout(() => setCopied(false), 2000);
  };

  const resultIcon = (result) => {
    if (result === "won") return <span className="bet-slip-result-icon bet-slip-result-won" title="Won">&#10003;</span>;
    if (result === "lost") return <span className="bet-slip-result-icon bet-slip-result-lost" title="Lost">&#10007;</span>;
    if (result === "void") return <span className="bet-slip-result-icon bet-slip-result-void" title="Void">&mdash;</span>;
    return null;
  };

  const resultBorderClass = (result) => {
    if (result === "won") return "bet-slip-pick-won";
    if (result === "lost") return "bet-slip-pick-lost";
    if (result === "void") return "bet-slip-pick-void";
    return "";
  };

  return (
    <div className="bet-slip">
      <div className="bet-slip-perforation" />
      <div className="bet-slip-inner">
        {/* Header */}
        <div className="bet-slip-header">
          <div className="bet-slip-header-title">ACCUMULATOR BET SLIP</div>
          <div className="bet-slip-header-meta">
            #{String(acca.id).padStart(5, "0")} | {new Date(acca.created_at).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}
            {isSettled && (
              <span className={`bet-slip-status bet-slip-status-${acca.status}`}>
                {acca.status.toUpperCase()}
              </span>
            )}
          </div>
        </div>

        {/* Picks */}
        <div className="bet-slip-picks">
          {acca.bets.map((bet, index) => (
            <div key={bet.id} className={`bet-slip-pick-item ${resultBorderClass(bet.result)}`}>
              <div className="bet-slip-pick-row">
                <span className="bet-slip-pick-number">{index + 1}.</span>
                <span className="bet-slip-pick-description">{bet.description}</span>
                <span className="bet-slip-pick-leader" />
                <span className="bet-slip-pick-odds">{formatOdds(bet.odds, oddsFormat)}</span>
                {resultIcon(bet.result)}
              </div>
              <div className="bet-slip-pick-meta">
                {bet.commence_time && (
                  <span>{formatKickoffTime(bet.commence_time)}</span>
                )}
                <span>Picked by {bet.username}</span>
              </div>
              {acca.status === "open" && user && bet.user_id === user.id && onRemovePick && (
                <button
                  className="bet-slip-remove-btn"
                  onClick={() => onRemovePick(bet.id)}
                >
                  REMOVE
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="bet-slip-summary">
          <div className="bet-slip-summary-row">
            <span>COMBINED ODDS</span>
            <span className="bet-slip-summary-leader" />
            <span className="bet-slip-total-odds">{formatOdds(combinedOdds, oddsFormat)}</span>
          </div>
          {bestBookmaker && (
            <div className="bet-slip-summary-row">
              <span>BEST BOOKMAKER</span>
              <span className="bet-slip-summary-leader" />
              <span className="bet-slip-bookmaker-name">
                {bestBookmaker}
                {!isSettled && bestBookmakerUrl && (
                  <a
                    href={bestBookmakerUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bet-slip-bookmaker-link"
                    onClick={() => api.trackBookmakerClick(bestBookmakerKey, acca.id, "betslip")}
                  >
                    Visit
                  </a>
                )}
              </span>
            </div>
          )}
          {!bookmakerComparison && acca.status === "open" && (
            <p className="bet-slip-hint">Compare bookmakers above for best odds</p>
          )}
        </div>

        {/* Copy Button */}
        {!isSettled && (
          <button className={`btn-copy${copied ? " btn-copy-success" : ""}`} onClick={handleCopy}>
            {copied ? "COPIED!" : "COPY TO CLIPBOARD"}
          </button>
        )}

        {error && <div className="bet-slip-error">{error}</div>}

        {/* Footer meta */}
        {(acca.leagues || acca.match_dates) && (
          <div className="bet-slip-meta">
            {acca.leagues && acca.leagues.map(k => LEAGUE_NAME_MAP[k] || k).join(", ")}
            {acca.leagues && acca.match_dates && " | "}
            {acca.match_dates && [...acca.match_dates].sort().map(d => formatDisplayDate(d)).join(", ")}
          </div>
        )}

        {/* Barcode decoration */}
        <div className="bet-slip-barcode" aria-hidden="true" />
      </div>
    </div>
  );
}
