import { useState, useRef } from "react";
import { formatOdds } from "../utils/formatters";
import { getBttsOdds } from "../api/client";

export default function FixtureCard({ match, fixtureTaken, takenBet, onPickMatch, isSubmitting, oddsFormat }) {
  const [expanded, setExpanded] = useState(false);
  const [bttsData, setBttsData] = useState(null);
  const [loadingBtts, setLoadingBtts] = useState(false);
  const fetchingRef = useRef(false);

  const kickoff = new Date(match.commence_time).toLocaleTimeString("en-GB", {
    hour: "2-digit", minute: "2-digit",
  });

  const toggleExpanded = async () => {
    const willExpand = !expanded;
    setExpanded(willExpand);
    if (willExpand && !bttsData && !fetchingRef.current && !match.btts_yes) {
      fetchingRef.current = true;
      setLoadingBtts(true);
      try {
        const data = await getBttsOdds(match.id, match.league);
        setBttsData(data);
      } catch (err) {
        // BTTS not available for this match — silently ignore
      } finally {
        fetchingRef.current = false;
        setLoadingBtts(false);
      }
    }
  };

  // Merge btts data onto match for pick handler
  const matchWithBtts = bttsData
    ? { ...match, btts_yes: bttsData.btts_yes, btts_no: bttsData.btts_no }
    : match;

  return (
    <div className={`fixture-card${fixtureTaken ? " fixture-card-taken" : ""}`}>
      {/* taken banner */}
      {fixtureTaken && takenBet && (
        <div className="fixture-taken-banner">
          Picked by {takenBet.username}: {takenBet.description}
        </div>
      )}

      {/* teams row */}
      <div className="fixture-teams-row">
        <span className="fixture-team">{match.home_team}</span>
        <span className="fixture-kickoff">{kickoff}</span>
        <span className="fixture-team fixture-team-away">{match.away_team}</span>
      </div>

      {/* h2h odds row */}
      <div className="fixture-odds-row">
        <button
          className={`fixture-odds-btn${fixtureTaken ? " fixture-odds-taken" : ""}`}
          onClick={() => !fixtureTaken && onPickMatch(match, "home")}
          disabled={fixtureTaken || isSubmitting}
        >
          <div className="fixture-odds-label">{fixtureTaken ? "Taken" : "Home"}</div>
          <div className={fixtureTaken ? "fixture-odds-value-taken" : "fixture-odds-value"}>
            {formatOdds(match.home_odds, oddsFormat)}
          </div>
        </button>
        <button
          className={`fixture-odds-btn${fixtureTaken ? " fixture-odds-taken" : ""}`}
          onClick={() => !fixtureTaken && onPickMatch(match, "draw")}
          disabled={fixtureTaken || isSubmitting}
        >
          <div className="fixture-odds-label">{fixtureTaken ? "Taken" : "Draw"}</div>
          <div className={fixtureTaken ? "fixture-odds-value-taken" : "fixture-odds-value"}>
            {formatOdds(match.draw_odds, oddsFormat)}
          </div>
        </button>
        <button
          className={`fixture-odds-btn${fixtureTaken ? " fixture-odds-taken" : ""}`}
          onClick={() => !fixtureTaken && onPickMatch(match, "away")}
          disabled={fixtureTaken || isSubmitting}
        >
          <div className="fixture-odds-label">{fixtureTaken ? "Taken" : "Away"}</div>
          <div className={fixtureTaken ? "fixture-odds-value-taken" : "fixture-odds-value"}>
            {formatOdds(match.away_odds, oddsFormat)}
          </div>
        </button>
      </div>

      {/* More bets toggle */}
      {!fixtureTaken && (
        <>
          <button className="fixture-more-bets-toggle" onClick={toggleExpanded}>
            {expanded ? "Less bets" : "More bets"}
          </button>
          {expanded && (
            <div className="fixture-extra-odds">
              {/* BTTS section - show loading, or lazy-loaded data, or pre-existing match data */}
              {loadingBtts && (
                <p className="text-muted fixture-loading-btts">Loading BTTS odds...</p>
              )}
              {!loadingBtts && (bttsData?.btts_yes != null || match.btts_yes != null) && (
                <div className="fixture-extra-odds-row">
                  <button
                    className="fixture-odds-btn"
                    onClick={() => onPickMatch(matchWithBtts, "btts_yes")}
                    disabled={isSubmitting}
                  >
                    <div className="fixture-odds-label">BTTS Yes</div>
                    <div className="fixture-odds-value">
                      {formatOdds(bttsData?.btts_yes ?? match.btts_yes, oddsFormat)}
                    </div>
                  </button>
                  <button
                    className="fixture-odds-btn"
                    onClick={() => onPickMatch(matchWithBtts, "btts_no")}
                    disabled={isSubmitting}
                  >
                    <div className="fixture-odds-label">BTTS No</div>
                    <div className="fixture-odds-value">
                      {formatOdds(bttsData?.btts_no ?? match.btts_no, oddsFormat)}
                    </div>
                  </button>
                </div>
              )}
              {/* Over/Under section */}
              {match.over_2_5 != null && (
                <div className="fixture-extra-odds-row">
                  <button
                    className="fixture-odds-btn"
                    onClick={() => onPickMatch(match, "over_2_5")}
                    disabled={isSubmitting}
                  >
                    <div className="fixture-odds-label">Over {match.totals_line}</div>
                    <div className="fixture-odds-value">{formatOdds(match.over_2_5, oddsFormat)}</div>
                  </button>
                  <button
                    className="fixture-odds-btn"
                    onClick={() => onPickMatch(match, "under_2_5")}
                    disabled={isSubmitting}
                  >
                    <div className="fixture-odds-label">Under {match.totals_line}</div>
                    <div className="fixture-odds-value">{formatOdds(match.under_2_5, oddsFormat)}</div>
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
