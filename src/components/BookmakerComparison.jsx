import { BOOKMAKER_URLS, BOOKMAKER_DISPLAY_NAMES } from "../utils/constants";

export default function BookmakerComparison({ data }) {
  if (!data || typeof data !== "object") return null;

  const entries = Object.entries(data)
    .filter(([, d]) => d && typeof d.total_odds === 'number')
    .sort((a, b) => b[1].total_odds - a[1].total_odds);
  if (entries.length === 0) return null;

  const bestOdds = entries[0][1].total_odds;

  return (
    <div className="bookmaker-section">
      <h3 className="bookmaker-section-title">Bookmaker Comparison</h3>
      <p className="bookmaker-section-desc">
        See which bookmaker offers the best odds for your complete acca:
      </p>
      <div>
        {entries.map(([bookmaker, d]) => {
          const isBest = d.total_odds === bestOdds;
          const url = BOOKMAKER_URLS[bookmaker];

          const content = (
            <>
              <div className="bookmaker-info">
                <strong
                  className={isBest ? "bookmaker-name bookmaker-name-best" : "bookmaker-name bookmaker-name-other"}
                >
                  {BOOKMAKER_DISPLAY_NAMES[bookmaker] || bookmaker}
                </strong>
                <span className={isBest ? "bookmaker-odds-best" : "bookmaker-odds-other"}>
                  {d.total_odds}x {isBest && "BEST"}
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
        })}
      </div>
    </div>
  );
}
