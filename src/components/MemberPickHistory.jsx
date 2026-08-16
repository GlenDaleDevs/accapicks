import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import * as api from "../api/client";
import { accaDetail, groupTable } from "../utils/routes";
import { useApp } from "../context/AppContext";
import { weekLabelShort } from "../utils/week";
import Skeleton from "./Skeleton";

export default function MemberPickHistory() {
  const { groupId, userId } = useParams();
  const navigate = useNavigate();
  const { groups } = useApp();
  const seasonStart = groups.find((g) => String(g.id) === String(groupId))?.season_start_date;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const result = await api.getMemberPicks(groupId, userId);
        setData(result);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load pick history");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [groupId, userId]);

  if (loading) {
    return (
      <div>
        <button className="btn btn-ghost mb-20" disabled>&larr; Back</button>
        <Skeleton width="200px" height="24px" count={1} />
        <div className="skeleton-spacer">
          <Skeleton width="100%" height="80px" count={2} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <button className="btn btn-ghost mb-20" onClick={() => navigate(groupTable(groupId))}>
          &larr; Back to Group
        </button>
        <div className="alert-error">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const { summary, picks } = data;

  // Group picks by acca
  const picksByAcca = {};
  for (const pick of picks) {
    if (!picksByAcca[pick.acca_id]) {
      picksByAcca[pick.acca_id] = {
        acca_name: pick.acca_name,
        acca_round_number: pick.acca_round_number,
        week_number: pick.acca_week_number,
        round_number: pick.acca_round_number,
        acca_status: pick.acca_status,
        acca_id: pick.acca_id,
        picks: [],
      };
    }
    picksByAcca[pick.acca_id].picks.push(pick);
  }

  const accaOutcomeText = (accaGroup) => {
    const { acca_status: status, acca_legs: legs, acca_landed: landed } = accaGroup;
    const tally = legs ? ` — ${landed} of ${legs} landed` : "";
    if (status === "won") return `Acca won${tally}`;
    if (status === "lost") return `Acca lost${tally}`;
    if (status === "settled") return `Acca settled${tally}`;
    if (status === "locked") return "Acca in play";
    return "Acca still open";
  };

  const resultBadgeClass = (result) => {
    if (result === "won") return "pick-result-badge pick-result-won";
    if (result === "lost") return "pick-result-badge pick-result-lost";
    if (result === "void") return "pick-result-badge pick-result-void";
    return "pick-result-badge pick-result-pending";
  };

  return (
    <div className="page-content">
      <button className="btn btn-ghost mb-20" onClick={() => navigate(groupTable(groupId))}>
        &larr; Back to Group
      </button>

      <h2 className="section-title">{data.username}'s Picks</h2>

      {/* Same scope as the table that linked here — otherwise a row reading
          3–1 opens onto a career history and looks like a bug. */}
      {seasonStart && (
        <p className="league-season-note">
          Counting from {new Date(`${seasonStart}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
        </p>
      )}

      <div className="member-history-summary">
        <div className="summary-stat">
          <span className="summary-stat-value">{summary.total_bets}</span>
          <span className="summary-stat-label">Total</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-value summary-stat-won">{summary.won}</span>
          <span className="summary-stat-label">Won</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-value summary-stat-lost">{summary.lost}</span>
          <span className="summary-stat-label">Lost</span>
        </div>
        <div className="summary-stat">
          <span className="summary-stat-value">{summary.win_rate}%</span>
          <span className="summary-stat-label">Win Rate</span>
        </div>
        {summary.best_odds_won > 0 && (
          <div className="summary-stat">
            <span className="summary-stat-value">{summary.best_odds_won}</span>
            <span className="summary-stat-label">Best Odds</span>
          </div>
        )}
        {summary.longest_win_streak > 0 && (
          <div className="summary-stat">
            <span className="summary-stat-value">🔥{summary.longest_win_streak}</span>
            <span className="summary-stat-label">Best Streak</span>
          </div>
        )}
      </div>

      {picks.length === 0 ? (
        <p className="empty-state">
          No picks yet
          <span className="empty-state-hint">This member hasn't added any picks to accas in this group.</span>
        </p>
      ) : (
        Object.values(picksByAcca).map((accaGroup) => (
          <div key={accaGroup.acca_id} className="member-acca-group">
            <div
              className="member-acca-header"
              onClick={() => navigate(accaDetail(groupId, accaGroup.acca_id))}
            >
              <span className="member-acca-name">
                {accaGroup.acca_round_number ? weekLabelShort(accaGroup) : accaGroup.acca_name}
              </span>
            </div>

            {/* On a personal profile the person's own pick is the headline.
                The acca's own result is a muted strip that explains itself —
                a bare LOST above a WON pick reads as a bug. */}
            <div className={`member-acca-outcome member-acca-outcome-${accaGroup.acca_status}`}>
              {accaOutcomeText(accaGroup)}
            </div>
            {accaGroup.picks.map((pick) => (
              <div key={pick.bet_id} className="member-pick-item">
                <div className="member-pick-main">
                  <span className="member-pick-desc">{pick.description}</span>
                  <span className={resultBadgeClass(pick.result)}>
                    {pick.result || "pending"}
                  </span>
                </div>
                <div className="member-pick-meta">
                  <span>Odds: {pick.odds}</span>
                  {pick.commence_time && (
                    <span>
                      {new Date(pick.commence_time).toLocaleDateString("en-GB", {
                        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
                      })}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  );
}
