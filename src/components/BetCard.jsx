export default function BetCard({ bet, accaStatus, isOwnBet, onRemove, onMarkResult }) {
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

  return (
    <div className={`bet-card ${cardClass}`}>
      <div className="bet-card-header">
        <div>
          <strong className="bet-description">{bet.description}</strong>
          <p className="bet-picked-by">Picked by: {bet.username}</p>
        </div>
        <div className="text-right">
          <div className="bet-odds">{bet.odds}</div>
          {bet.result && (
            <span className={`bet-result ${resultClass}`}>
              {bet.result.toUpperCase()}
            </span>
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

      {!bet.result && (
        <div className="bet-result-buttons">
          <button
            className="btn btn-success btn-sm"
            onClick={() => onMarkResult(bet.id, "won")}
          >
            Won
          </button>
          <button
            className="btn btn-danger btn-sm"
            onClick={() => onMarkResult(bet.id, "lost")}
          >
            Lost
          </button>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => onMarkResult(bet.id, "void")}
          >
            Void
          </button>
        </div>
      )}
    </div>
  );
}
