import Skeleton from "./Skeleton";

export default function Leaderboard({ leaderboard, loading, accas }) {
  const formatBestOdds = (odds) => {
    if (!odds || odds === 0) return "-";
    return odds.toFixed(2);
  };

  return (
    <div className="leaderboard-container">
      <h3 className="section-title">Group Leaderboard</h3>
      {loading ? (
        <div>
          <Skeleton width="100%" height="60px" count={3} />
        </div>
      ) : leaderboard.length === 0 ? (
        <p className="empty-state">
          No stats yet. Start placing bets and marking results!
        </p>
      ) : (
        <div>
          {leaderboard.map((entry, index) => (
            <div
              key={entry.user_id}
              className={`leaderboard-row${entry.rank === 1 ? " leaderboard-row-first" : ""}`}
            >
              <div>
                <strong className="leaderboard-rank">
                  {entry.rank ?? index + 1}. {entry.username}
                </strong>
                <p className="leaderboard-record">
                  {entry.won}W - {entry.lost}L - {entry.pending}P
                </p>
              </div>
              <div className="text-right">
                <div
                  className={`leaderboard-winrate ${entry.rank === 1 ? "leaderboard-winrate-first" : "leaderboard-winrate-other"}`}
                >
                  {entry.win_rate}%
                </div>
                <p className="leaderboard-total">
                  Best: {formatBestOdds(entry.best_odds_won)}
                </p>
                <p className="leaderboard-total">
                  {entry.total_bets} total bets
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
