import { useState } from "react";
import { BOOKMAKER_DISPLAY_NAMES } from "../utils/constants";
import { formatOdds } from "../utils/formatters";
import * as api from "../api/client";

const DEFAULT_VISIBLE = 5;

export default function BookmakerComparison({ data, oddsFormat = "decimal", bookmakerLinks = {}, accaId }) {
  const [showAll, setShowAll] = useState(false);

  if (!data || typeof data !== "object") return null;

  const entries = Object.entries(data)
    .filter(([, d]) => d && typeof d.total_odds === 'number')
    .sort((a, b) => b[1].total_odds - a[1].total_odds);
  if (entries.length === 0) return null;

  const bestOdds = entries[0][1].total_odds;
  const visibleEntries = showAll ? entries : entries.slice(0, DEFAULT_VISIBLE);
  const hiddenCount = entries.length - DEFAULT_VISIBLE;

  const renderRow = ([bookmaker, d]) => {
    const isBest = d.total_odds === bestOdds;
    const rawUrl = bookmakerLinks[bookmaker]?.url;
    // Only https links become clickable — a javascript:/data: URL in the
    // affiliate config would otherwise render as a script sink (React only
    // warns, doesn't block). Anything else falls through to the plain row.
    const url = typeof rawUrl === "string" && rawUrl.startsWith("https://") ? rawUrl : null;
    const displayName = bookmakerLinks[bookmaker]?.display_name || BOOKMAKER_DISPLAY_NAMES[bookmaker] || bookmaker;

    const content = (
      <>
        <div className="bookmaker-info">
          <span className="bookmaker-name-wrapper">
            <strong
              className={isBest ? "bookmaker-name bookmaker-name-best" : "bookmaker-name bookmaker-name-other"}
            >
              {displayName}
            </strong>
            {d.estimated && <span className="bookmaker-est-badge">est.</span>}
          </span>
          <span className={isBest ? "bookmaker-odds-best" : "bookmaker-odds-other"}>
            {d.estimated && "~"}{formatOdds(d.total_odds, oddsFormat)} {isBest && "BEST"}
          </span>
        </div>
        {url && (
          <span className="bookmaker-visit">
            Visit →
          </span>
        )}
      </>
    );

    if (url) {
      return (
        <a
          key={bookmaker}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className={`bookmaker-row bookmaker-row-link ${isBest ? "bookmaker-row-best" : "bookmaker-row-other"}`}
          onClick={() => api.trackBookmakerClick(bookmaker, accaId, "comparison")}
        >
          {content}
        </a>
      );
    }

    return (
      <div
        key={bookmaker}
        className={`bookmaker-row ${isBest ? "bookmaker-row-best" : "bookmaker-row-other"}`}
      >
        {content}
      </div>
    );
  };

  return (
    <div className="bookmaker-section">
      <h3 className="bookmaker-section-title">Bookmaker Comparison</h3>
      <p className="bookmaker-section-desc">
        See which bookmaker offers the best odds for your complete acca:
      </p>
      <div>
        {visibleEntries.map(renderRow)}
      </div>
      {hiddenCount > 0 && (
        <button
          className="bookmaker-show-more"
          onClick={() => setShowAll(!showAll)}
        >
          {showAll ? "Show fewer sites" : `Show all ${entries.length} bookmakers`}
        </button>
      )}
      {entries.some(([, d]) => d.estimated) && (
        <p className="text-muted mt-8" style={{ fontSize: "0.8rem" }}>
          Odds marked with ~ are estimated from your picked odds (3% below). Actual odds may vary.
        </p>
      )}
    </div>
  );
}
