import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import * as api from "../api/client";
import Leaderboard from "./Leaderboard";
import { useApp } from "../context/AppContext";

export default function TableTab() {
  const { groupId } = useParams();
  const { groups } = useApp();

  const [leaderboard, setLeaderboard] = useState([]);
  const [accaStats, setAccaStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const group = groups.find((g) => String(g.id) === String(groupId));

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [lb, stats] = await Promise.all([
          api.getGroupLeaderboard(groupId),
          api.getGroupAccaStats(groupId).catch(() => null),
        ]);
        if (cancelled) return;
        setLeaderboard(lb);
        setAccaStats(stats);
      } catch (err) {
        console.error("Failed to load leaderboard:", err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [groupId]);

  return (
    <div className="table-tab">
      <h2 className="section-title">{group?.name || "Table"}</h2>
      <Leaderboard
        leaderboard={leaderboard}
        loading={loading}
        groupId={groupId}
        accaStats={accaStats}
        seasonStart={group?.season_start_date}
        title={null}
      />
    </div>
  );
}
