export default function MiniLeaderboard({ entries }) {
  if (!entries || entries.length === 0) {
    return <div className="mini-lb-empty">No picks yet</div>;
  }

  return (
    <div className="mini-lb">
      {entries.slice(0, 3).map((entry, idx) => (
        <div key={entry.user_id} className="mini-lb-row">
          <span className={`mini-lb-pos${entry.rank === 1 ? " mini-lb-pos-first" : ""}`}>
            {entry.rank ?? idx + 1}
          </span>
          <span className="mini-lb-name">{entry.username}</span>
        </div>
      ))}
    </div>
  );
}
