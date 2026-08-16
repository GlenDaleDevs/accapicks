/**
 * How a week is named.
 *
 * `round_number` is a per-group counter that never resets, so by a group's
 * third season it reads "Week 34". `week_number` is the position within the
 * current season, which is what anyone actually means by "Week 3" — so that's
 * what gets shown.
 *
 * Accas from a previous season have no `week_number`. They keep the number they
 * were given at the time, marked so it can't be mistaken for this season's.
 */
export function weekLabel(acca) {
  if (!acca) return "No week yet";
  if (acca.week_number) return `Week ${acca.week_number}`;
  if (acca.round_number) return `Week ${acca.round_number} · past season`;
  return "No week yet";
}

/** Short form for tight spaces — no "past season" suffix. */
export function weekLabelShort(acca) {
  const number = acca?.week_number || acca?.round_number;
  return number ? `Week ${number}` : acca?.name || "Week";
}
