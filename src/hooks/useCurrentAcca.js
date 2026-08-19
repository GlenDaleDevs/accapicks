import { useEffect, useState } from "react";
import * as api from "../api/client";
import { resolveCurrent } from "../utils/accaState";

// The group's current acca with its bets, for surfaces outside the Acca tab.
// Keyed on the group only — never the browsed week — so stepping through
// fixture weeks can't re-fetch and trip the endpoint's rate limit.
export default function useCurrentAcca(groupId) {
  // The group id is stored with the result so a stale acca is never returned
  // for a different group — no synchronous reset needed on group change.
  const [loaded, setLoaded] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const accas = await api.getAccasByGroup(groupId);
        const current = resolveCurrent(accas);
        if (!current || cancelled) return;
        const detail = await api.getAccaById(current.id);
        if (!cancelled) setLoaded({ groupId, acca: detail });
      } catch {
        // A 403 (user left the group) or a blip: the caller's surface must
        // stay browsable, it just offers no picks.
      }
    })();
    return () => { cancelled = true; };
  }, [groupId]);

  return loaded && loaded.groupId === groupId ? loaded.acca : null;
}
