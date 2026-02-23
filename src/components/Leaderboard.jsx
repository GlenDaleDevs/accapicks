import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { staggerContainer, leaderboardRowVariants } from "../utils/animations";
import Skeleton from "./Skeleton";

export default function Leaderboard({ leaderboard, loading, accas, groupId, accaStats, title = "Group Leaderboard" }) {
  const navigate = useNavigate();

  return (
    <div className="leaderboard-container">
      {title !== null && <h3 className="section-title">{title}</h3>}
      {accaStats && (accaStats.won_accas > 0 || accaStats.lost_accas > 0) && (
        <div className="group-stats-bar">
          <span className="group-stats-record">
            Group Record: <strong>{accaStats.won_accas}W</strong> - <strong>{accaStats.lost_accas}L</strong>
            {" "}({accaStats.success_rate}%)
          </span>
          {accaStats.open_accas > 0 && (
            <span className="group-stats-open">{accaStats.open_accas} open</span>
          )}
          {accaStats.locked_accas > 0 && (
            <span className="group-stats-locked">{accaStats.locked_accas} active</span>
          )}
        </div>
      )}
      {loading ? (
        <div>
          <Skeleton width="100%" height="60px" count={3} />
        </div>
      ) : leaderboard.length === 0 ? (
        <p className="empty-state">
          No stats yet — results update automatically after matches finish.
          <span className="empty-state-hint">Create an acca and add your picks to get started.</span>
        </p>
      ) : (
        <motion.div
          className="league-table"
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          <div className="league-table-header">
            <div className="league-col league-col-pos">#</div>
            <div className="league-col league-col-name">Name</div>
            <div className="league-col league-col-streak" title="Current streak">🔥</div>
            <div className="league-col league-col-stat">W</div>
            <div className="league-col league-col-stat">L</div>
            <div className="league-col league-col-winrate">Win %</div>
          </div>
          {leaderboard.map((entry, index) => {
            const rank = entry.rank ?? index + 1;
            const rowRankClass = rank <= 3 ? ` league-table-row-${["first","second","third"][rank - 1]}` : "";
            const posRankClass = rank <= 3 ? ` league-pos-${["first","second","third"][rank - 1]}` : "";
            return (
              <motion.div
                key={entry.user_id}
                className={`league-table-row${rowRankClass}`}
                variants={leaderboardRowVariants}
                layout
                onClick={() => navigate(`/groups/${groupId}/members/${entry.user_id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); navigate(`/groups/${groupId}/members/${entry.user_id}`); } }}
                style={(() => {
                  const count = entry.streak_count || 0;
                  const type = entry.streak_type;
                  if (count < 2 || type === "none") return undefined;
                  const alpha = Math.min(0.07 + (count - 2) * 0.04, 0.19);
                  if (type === "win") return { background: `linear-gradient(90deg, rgba(255, 140, 0, ${alpha}), transparent)` };
                  if (type === "loss") return { background: `linear-gradient(90deg, rgba(96, 165, 250, ${alpha}), transparent)` };
                  return undefined;
                })()}
              >
                <div className="league-col league-col-pos">
                  <span className={`league-pos${posRankClass}`}>
                    {rank}
                  </span>
                </div>
                <div className="league-col league-col-name">{entry.username}</div>
                <div className="league-col league-col-streak">
                  {entry.streak_count > 0 && entry.streak_type !== "none" && (
                    <span className={`league-streak league-streak-${entry.streak_type}`}>
                      {entry.streak_type === "win" ? "🔥" : "🧊"}{entry.streak_count}
                    </span>
                  )}
                </div>
                <div className="league-col league-col-stat">{entry.won}</div>
                <div className="league-col league-col-stat">{entry.lost}</div>
                <div className="league-col league-col-winrate">
                  <span className={`league-winrate${rank === 1 ? " league-winrate-first" : ""}`}>
                    {entry.win_rate}%
                  </span>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
}
