import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import * as api from "../api/client";
import Skeleton from "./Skeleton";

export default function MemberPickHistory({ user }) {
  const { groupId, userId } = useParams();
  const navigate = useNavigate();
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
        <button className="btn btn-ghost mb-20" onClick={() => navigate(`/groups/${groupId}`)}>
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
        acca_status: pick.acca_status,
        acca_id: pick.acca_id,
        picks: [],
      };
    }
    picksByAcca[pick.acca_id].picks.push(pick);
  }

  const resultBadgeClass = (result) => {
    if (result === "won") return "pick-result-badge pick-result-won";
    if (result === "lost") return "pick-result-badge pick-result-lost";
    if (result === "void") return "pick-result-badge pick-result-void";
    return "pick-result-badge pick-result-pending";
  };

  return (
    <div className="page-content">
      <button className="btn btn-ghost mb-20" onClick={() => navigate(`/groups/${groupId}`)}>
        &larr; Back to Group
      </button>

      <h2 className="section-title">{data.username}'s Picks</h2>

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
              onClick={() => navigate(`/groups/${groupId}/accas/${accaGroup.acca_id}`)}
            >
              <span className="member-acca-name">{accaGroup.acca_name}</span>
              <span className={`badge badge-${accaGroup.acca_status}`}>
                {accaGroup.acca_status.toUpperCase()}
              </span>
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
