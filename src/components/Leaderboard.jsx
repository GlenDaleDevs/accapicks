import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { staggerContainer, leaderboardRowVariants } from "../utils/animations";
import { memberPicks } from "../utils/routes";
import Skeleton from "./Skeleton";

// Below 2 a "streak" is just the last result, which nearly every row has.
const STREAK_MIN = 2;

function Movement({ change }) {
  if (change === null || change === undefined) return null;
  if (change > 0) return <span className="league-move league-move-up" title={`Up ${change}`}>▲</span>;
  if (change < 0) return <span className="league-move league-move-down" title={`Down ${-change}`}>▼</span>;
  return <span className="league-move league-move-level" title="No change">–</span>;
}

export default function Leaderboard({ leaderboard, loading, groupId, accaStats, title = "Group Leaderboard" }) {
  const navigate = useNavigate();

  // Only reserve the movement column once there's real movement to show.
  const hasMovement = leaderboard.some(
    (e) => e.rank_change !== null && e.rank_change !== undefined,
  );
  const gridClass = hasMovement ? "league-table-grid-move" : "league-table-grid";

  return (
    <div className="leaderboard-container">
      {title !== null && <h3 className="section-title">{title}</h3>}

      {/* "Accas won" not "Group Record: 0W-3L" — this counts whole accas,
          while the Picks column below counts individual picks. Same letters,
          different unit, same card. */}
      {accaStats && (accaStats.won_accas > 0 || accaStats.lost_accas > 0) && (
        <div className="group-stats-bar">
          <span className="group-stats-record">
            Accas won <strong>{accaStats.won_accas}/{accaStats.won_accas + accaStats.lost_accas}</strong>
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
          <div className={`league-table-header ${gridClass}`}>
            <div className="league-col league-col-pos">#</div>
            {hasMovement && <div className="league-col league-col-move" aria-label="Movement" />}
            <div className="league-col league-col-name">Name</div>
            <div className="league-col league-col-record" title="Picks won–lost">Picks</div>
            <div className="league-col league-col-winrate">Win %</div>
          </div>

          {leaderboard.map((entry, index) => {
            const rank = entry.rank ?? index + 1;
            const rowRankClass = rank <= 3 ? ` league-table-row-${["first", "second", "third"][rank - 1]}` : "";
            const posRankClass = rank <= 3 ? ` league-pos-${["first", "second", "third"][rank - 1]}` : "";
            const streakCount = entry.streak_count || 0;
            const streakType = entry.streak_type;
            const showStreak = streakCount >= STREAK_MIN && streakType !== "none";
            const streakClass = showStreak
              ? ` league-table-row-streak league-table-row-streak-${streakType === "win" ? "fire" : "ice"} streak-intensity-${Math.min(streakCount, 5)}`
              : "";
            const goToMember = () => navigate(memberPicks(groupId, entry.user_id));

            return (
              <motion.div
                key={entry.user_id}
                className={`league-table-row ${gridClass}${rowRankClass}${streakClass}`}
                variants={leaderboardRowVariants}
                layout
                onClick={goToMember}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); goToMember(); }
                }}
              >
                <div className="league-col league-col-pos">
                  <span className={`league-pos${posRankClass}`}>{rank}</span>
                </div>

                {hasMovement && (
                  <div className="league-col league-col-move">
                    <Movement change={entry.rank_change} />
                  </div>
                )}

                {/* Streak moves inline with the name, freeing a whole column.
                    Names are the content in a social app — they must not truncate. */}
                <div className="league-col league-col-name">
                  <span className="league-name-text">{entry.username}</span>
                  {showStreak && (
                    <span className={`league-streak league-streak-${streakType}`}>
                      {streakType === "win" ? "🔥" : "🧊"}{streakCount}
                    </span>
                  )}
                </div>

                <div className="league-col league-col-record">
                  {entry.won}<span className="league-record-sep">–</span>{entry.lost}
                </div>

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
