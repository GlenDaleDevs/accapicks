export default function BookmakerComparison({ data }) {
  if (!data || typeof data !== "object") return null;

  const entries = Object.entries(data);
  if (entries.length === 0) return null;

  const allOdds = entries.map(([, d]) => d.total_odds);
  const bestOdds = Math.max(...allOdds);

  return (
    <div className="bookmaker-section">
      <h3 className="bookmaker-section-title">Bookmaker Comparison</h3>
      <p className="bookmaker-section-desc">
        See which bookmaker offers the best odds for your complete acca:
      </p>
      <div>
        {entries.map(([bookmaker, d]) => {
          const isBest = d.total_odds === bestOdds;
          return (
            <div
              key={bookmaker}
              className={`bookmaker-row ${isBest ? "bookmaker-row-best" : "bookmaker-row-other"}`}
            >
              <strong
                className={isBest ? "bookmaker-name bookmaker-name-best" : "bookmaker-name bookmaker-name-other"}
              >
                {bookmaker}:
              </strong>
              <span className={isBest ? "bookmaker-odds-best" : "bookmaker-odds-other"}>
                {d.total_odds}x {isBest && "BEST"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
