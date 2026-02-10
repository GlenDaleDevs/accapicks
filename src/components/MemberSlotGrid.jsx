import { formatOdds } from "../utils/formatters";

export default function MemberSlotGrid({
  members,
  bets,
  currentUser,
  accaStatus,
  onAddPick,
  onRemovePick,
  oddsFormat = "decimal",
}) {
  if (!members || members.length === 0) return null;

  // Map user_id to bet
  const betByUser = {};
  (bets || []).forEach((b) => {
    betByUser[b.user_id] = b;
  });

  // Sort: current user first, then alphabetical
  const sorted = [...members].sort((a, b) => {
    if (currentUser && a.user_id === currentUser.id) return -1;
    if (currentUser && b.user_id === currentUser.id) return 1;
    return a.username.localeCompare(b.username);
  });

  return (
    <div className="member-slot-grid">
      {sorted.map((member) => {
        const bet = betByUser[member.user_id];
        const isSelf = currentUser && member.user_id === currentUser.id;
        const isOpen = accaStatus === "open";

        if (bet) {
          // Filled slot
          return (
            <div key={member.user_id} className="member-slot member-slot-filled">
              <div className="member-slot-header">
                <span className="member-slot-username">{member.username}</span>
                <span className="member-slot-odds">{formatOdds(bet.odds, oddsFormat)}</span>
              </div>
              <div className="member-slot-description">{bet.description}</div>
              {isSelf && isOpen && (
                <button
                  className="btn-remove-pick mt-8"
                  onClick={() => onRemovePick(bet.id)}
                >
                  Remove Pick
                </button>
              )}
            </div>
          );
        }

        // Empty slot - check if missed (acca not open)
        if (!isOpen) {
          return (
            <div key={member.user_id} className="member-slot member-slot-missed">
              <span className="member-slot-username">{member.username}</span>
              <span className="member-slot-missed-text">Missed their shot</span>
            </div>
          );
        }

        // Empty, open acca
        if (isSelf) {
          return (
            <div
              key={member.user_id}
              className="member-slot member-slot-empty member-slot-self"
              onClick={onAddPick}
              role="button"
              tabIndex={0}
            >
              <span className="member-slot-username">{member.username}</span>
              <span className="member-slot-cta">+ Add your pick</span>
            </div>
          );
        }

        return (
          <div key={member.user_id} className="member-slot member-slot-empty">
            <span className="member-slot-username">{member.username}</span>
            <span className="member-slot-waiting">Waiting for pick...</span>
          </div>
        );
      })}
    </div>
  );
}
