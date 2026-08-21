// GF and GA are hidden on narrow screens (see Standings.css) — position,
// record, goal difference and points are what the table is read for.
const COLUMNS = [
  { key: "played", label: "P" },
  { key: "won", label: "W" },
  { key: "drawn", label: "D" },
  { key: "lost", label: "L" },
  { key: "gf", label: "GF", wide: true },
  { key: "ga", label: "GA", wide: true },
  { key: "gd", label: "GD" },
  { key: "points", label: "Pts", strong: true },
];

function signed(value) {
  return value > 0 ? `+${value}` : String(value);
}

export default function StandingsTable({ rows, onTeam }) {
  return (
    <div className="standings-scroll">
      <table className="standings-table">
        <thead>
          <tr>
            <th className="standings-pos" scope="col">#</th>
            <th className="standings-team" scope="col">Team</th>
            {COLUMNS.map(({ key, label, wide }) => (
              <th key={key} scope="col" className={wide ? "standings-wide" : undefined}>
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.team}>
              <td className="standings-pos">{row.pos}</td>
              <th className="standings-team" scope="row">
                {onTeam ? (
                  <button
                    type="button"
                    className="standings-team-tap"
                    onClick={() => onTeam(row.team)}
                  >
                    {row.team}
                  </button>
                ) : (
                  row.team
                )}
              </th>
              {COLUMNS.map(({ key, wide, strong }) => (
                <td
                  key={key}
                  className={`${wide ? "standings-wide" : ""}${strong ? " standings-strong" : ""}`}
                >
                  {key === "gd" ? signed(row[key]) : row[key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
