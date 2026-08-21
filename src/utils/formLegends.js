// Dot meanings per tracker: [outcome letter, what it means]. Shared between
// FormDots.jsx (the dots themselves) and FixtureRow's FormKey / TeamDetail's
// header — kept in a plain module so it doesn't trip react-refresh's
// "component files only export components" rule.
export const LEGENDS = {
  results: [["W", "Won"], ["D", "Drew"], ["L", "Lost"]],
  btts: [["Y", "Both scored"], ["N", "Not both"]],
  over25: [["Y", "3+ goals"], ["N", "2 or fewer"]],
};
