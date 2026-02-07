import { formatOdds } from "../utils/formatters";

export default function BetCard({ bet, accaStatus, isOwnBet, onRemove, oddsFormat = "decimal" }) {
  const cardClass = bet.result === "won"
    ? "bet-card-won"
    : bet.result === "lost"
      ? "bet-card-lost"
      : bet.result === "void"
        ? "bet-card-void"
        : "bet-card-pending";

  const resultClass = bet.result === "won"
    ? "bet-result-won"
    : bet.result === "lost"
      ? "bet-result-lost"
      : "bet-result-void";

  // Determine if we should show pending auto-settlement indicator
  const showPendingIndicator = bet.event_id && !bet.result && accaStatus === "locked";

  return (
    <div className={`bet-card ${cardClass}`}>
      <div className="bet-card-header">
        <div>
          <strong className="bet-description">{bet.description}</strong>
          <p className="bet-picked-by">Picked by: {bet.username}</p>
        </div>
        <div className="text-right">
          <div className="bet-odds">{formatOdds(bet.odds, oddsFormat)}</div>
          {bet.result && (
            <span className={`bet-result ${resultClass}`}>
              {bet.result.toUpperCase()}
            </span>
          )}
          {showPendingIndicator && (
            <p className="bet-pending-result">Result pending...</p>
          )}
          {!bet.result && accaStatus === "open" && isOwnBet && (
            <button
              className="btn-remove-pick"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(bet.id);
              }}
            >
              Remove Pick
            </button>
          )}
        </div>
      </div>

    </div>
  );
}
