import { useState } from "react";
import * as api from "../../api/client";
import { useApp } from "../../context/AppContext";
import { showToast } from "../../utils/toast";
import BookmakerComparison from "../BookmakerComparison";

// The overhaul deleted AccaDetail and orphaned the bookmaker comparison;
// this is it rehomed at the foot of the slip. Button-triggered rather than
// automatic — a cache miss on the backend can cost odds-API credits, so it
// only runs when somebody actually asks.
export default function CompareBookmakers({ acca, oddsFormat }) {
  const { bookmakerLinks } = useApp();
  const [data, setData] = useState(null);
  const [comparing, setComparing] = useState(false);

  if (acca.status !== "open" || !(acca.bets || []).length) return null;

  const compare = async () => {
    setComparing(true);
    setData(null);
    try {
      const result = await api.compareBookmakers(acca.id);
      const priced = result && Object.values(result).some((d) => typeof d?.total_odds === "number");
      if (!priced) {
        // Best-effort feed (see gotchas.md) — say so rather than doing nothing
        showToast("No bookmaker prices available for this acca right now", "info");
      }
      setData(result);
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to compare bookmakers", "error");
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="compare-bookmakers">
      <button className="btn btn-secondary" onClick={compare} disabled={comparing}>
        {comparing ? "Comparing…" : "Compare bookmakers"}
      </button>
      <BookmakerComparison
        data={data}
        oddsFormat={oddsFormat}
        bookmakerLinks={bookmakerLinks}
        accaId={acca.id}
      />
    </div>
  );
}
