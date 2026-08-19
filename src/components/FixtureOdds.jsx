import { useRef, useState } from "react";
import { formatOdds } from "../utils/formatters";
import { getBttsOdds } from "../api/client";

// A single tappable price. Rendered greyed-out (still readable) when the
// fixture can't be picked — the odds are information either way.
export function OddsChip({ label, value, disabled, onClick, oddsFormat }) {
  if (value == null) return null;
  return (
    <button type="button" className="odds-chip" disabled={disabled} onClick={onClick}>
      {label && <span className="odds-chip-label">{label}</span>}
      <span className="odds-chip-value">{formatOdds(value, oddsFormat)}</span>
    </button>
  );
}

// BTTS and Over/Under behind a tap. Over/Under arrives free with the bulk
// odds call; BTTS is NOT on the bulk endpoint (422) and costs one credit per
// fixture on the per-event endpoint, so it is fetched only when this opens —
// the server caches it for 24h.
export function MoreBets({ odds, onPick, submitting, oddsFormat }) {
  const [open, setOpen] = useState(false);
  const [btts, setBtts] = useState(null);
  const [loading, setLoading] = useState(false);
  const fetchingRef = useRef(false);

  const toggle = async () => {
    const willOpen = !open;
    setOpen(willOpen);
    if (willOpen && !btts && !fetchingRef.current && odds.btts_yes == null) {
      fetchingRef.current = true;
      setLoading(true);
      try {
        setBtts(await getBttsOdds(odds.id, odds.league));
      } catch {
        // BTTS simply isn't offered for this match
      } finally {
        fetchingRef.current = false;
        setLoading(false);
      }
    }
  };

  const merged = btts ? { ...odds, btts_yes: btts.btts_yes, btts_no: btts.btts_no } : odds;
  const chip = (label, value, type) => (
    <OddsChip
      label={label}
      value={value}
      disabled={submitting}
      onClick={() => onPick(merged, type)}
      oddsFormat={oddsFormat}
    />
  );

  return (
    <>
      <button type="button" className="more-bets-toggle" aria-expanded={open} onClick={toggle}>
        {open ? "Less bets" : "More bets"}
      </button>
      {open && (
        <div className="more-bets">
          {loading && <span className="more-bets-note">Loading BTTS odds…</span>}
          {!loading && merged.btts_yes != null && (
            <div className="more-bets-row">
              {chip("BTTS Yes", merged.btts_yes, "btts_yes")}
              {chip("BTTS No", merged.btts_no, "btts_no")}
            </div>
          )}
          {merged.over_2_5 != null && (
            <div className="more-bets-row">
              {chip(`Over ${merged.totals_line}`, merged.over_2_5, "over_2_5")}
              {chip(`Under ${merged.totals_line}`, merged.under_2_5, "under_2_5")}
            </div>
          )}
          {!loading && merged.btts_yes == null && merged.over_2_5 == null && (
            <span className="more-bets-note">No extra markets for this match</span>
          )}
        </div>
      )}
    </>
  );
}
