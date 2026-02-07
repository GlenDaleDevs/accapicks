import Skeleton from "./Skeleton";

export default function Leaderboard({ leaderboard, loading, accas }) {
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
        <div className="league-table">
          <div className="league-table-header">
            <div className="league-col league-col-pos">#</div>
            <div className="league-col league-col-name">Name</div>
            <div className="league-col league-col-stat">W</div>
            <div className="league-col league-col-stat">L</div>
            <div className="league-col league-col-winrate">Win %</div>
          </div>
          {leaderboard.map((entry, index) => (
            <div
              key={entry.user_id}
              className={`league-table-row${entry.rank === 1 ? " league-table-row-first" : ""}`}
            >
              <div className="league-col league-col-pos">
                <span className={`league-pos${entry.rank === 1 ? " league-pos-first" : ""}`}>
                  {entry.rank ?? index + 1}
                </span>
              </div>
              <div className="league-col league-col-name">{entry.username}</div>
              <div className="league-col league-col-stat">{entry.won}</div>
              <div className="league-col league-col-stat">{entry.lost}</div>
              <div className="league-col league-col-winrate">
                <span className={`league-winrate${entry.rank === 1 ? " league-winrate-first" : ""}`}>
                  {entry.win_rate}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
