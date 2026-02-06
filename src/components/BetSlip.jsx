import { useState } from "react";
import { BOOKMAKER_DISPLAY_NAMES } from "../utils/constants";
import { formatOdds, formatBetSlipText } from "../utils/formatters";
import * as api from "../api/client";

export default function BetSlip({ acca, oddsFormat, bookmakerComparison, bookmakerLinks = {} }) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  if (!acca || acca.bets.length === 0) return null;
  if (acca.status === "settled") return null;

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
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
      setError("Failed to copy to clipboard");
    }
  };

  return (
    <div className="bet-slip">
      <h3 className="section-title">Bet Slip</h3>

      <div className="bet-slip-picks">
        {acca.bets.map((bet, index) => (
          <div key={bet.id} className="bet-slip-pick-item">
            <span className="bet-slip-pick-number">{index + 1}.</span>
            <span className="bet-slip-pick-description">{bet.description}</span>
            <span className="bet-slip-pick-odds">@ {formatOdds(bet.odds, oddsFormat)}</span>
          </div>
        ))}
      </div>

      <div className="bet-slip-summary">
        <div className="bet-slip-combined-odds">
          Combined Odds: <strong>{formatOdds(combinedOdds, oddsFormat)}</strong>
        </div>

        {bestBookmaker && (
          <div className="bet-slip-best-bookmaker">
            Best Odds at: <strong>{bestBookmaker}</strong>
            {bestBookmakerUrl && (
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
          </div>
        )}

        {!bookmakerComparison && (
          <p className="bet-slip-hint">Compare bookmakers above for best odds</p>
        )}
      </div>

      <button className="btn-copy" onClick={handleCopy}>
        {copied ? "Copied!" : "Copy to Clipboard"}
      </button>

      {error && <div className="bet-slip-error">{error}</div>}
    </div>
  );
}
