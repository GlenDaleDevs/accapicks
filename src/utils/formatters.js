export const getDaysInMonth = (year, month) => {
  return new Date(year, month + 1, 0).getDate();
};

export const getFirstDayOfMonth = (year, month) => {
  const day = new Date(year, month, 1).getDay();
  return day === 0 ? 6 : day - 1;
};

export const formatDateStr = (year, month, day) => {
  const m = String(month + 1).padStart(2, "0");
  const d = String(day).padStart(2, "0");
  return `${year}-${m}-${d}`;
};

export const isDateInPast = (dateStr) => {
  const today = new Date();
  const todayStr = formatDateStr(
    today.getFullYear(),
    today.getMonth(),
    today.getDate(),
  );
  return dateStr < todayStr;
};

export const formatCountdown = (locksAtStr) => {
  if (!locksAtStr) return "";
  const locksAt = new Date(locksAtStr);
  const now = new Date();
  const diff = locksAt - now;
  if (diff <= 0) return "Locking...";
  const hours = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  const secs = Math.floor((diff % 60000) / 1000);
  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h remaining`;
  }
  if (hours > 0) return `${hours}h ${mins}m remaining`;
  return `${mins}m ${secs}s remaining`;
};

export const formatDisplayDate = (dateStr) => {
  const dt = new Date(dateStr + "T00:00:00");
  return dt.toLocaleDateString("en-GB", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
};

// Common UK bookmaker fractional odds (sorted by decimal value)
const COMMON_FRACTIONS = [
  { decimal: 1.10, fraction: "1/10" },
  { decimal: 1.20, fraction: "1/5" },
  { decimal: 1.25, fraction: "1/4" },
  { decimal: 1.33, fraction: "1/3" },
  { decimal: 1.40, fraction: "2/5" },
  { decimal: 1.50, fraction: "1/2" },
  { decimal: 1.57, fraction: "4/7" },
  { decimal: 1.62, fraction: "8/13" },
  { decimal: 1.67, fraction: "4/6" },
  { decimal: 1.73, fraction: "8/11" },
  { decimal: 1.80, fraction: "4/5" },
  { decimal: 1.83, fraction: "5/6" },
  { decimal: 1.91, fraction: "10/11" },
  { decimal: 2.00, fraction: "EVS" },
  { decimal: 2.10, fraction: "11/10" },
  { decimal: 2.20, fraction: "6/5" },
  { decimal: 2.25, fraction: "5/4" },
  { decimal: 2.38, fraction: "11/8" },
  { decimal: 2.50, fraction: "6/4" },
  { decimal: 2.63, fraction: "13/8" },
  { decimal: 2.75, fraction: "7/4" },
  { decimal: 2.88, fraction: "15/8" },
  { decimal: 3.00, fraction: "2/1" },
  { decimal: 3.25, fraction: "9/4" },
  { decimal: 3.50, fraction: "5/2" },
  { decimal: 3.75, fraction: "11/4" },
  { decimal: 4.00, fraction: "3/1" },
];

const decimalToFraction = (decimal) => {
  if (decimal <= 1) return "N/A";

  // For higher odds (4.0+), round to one decimal place X.X/1
  if (decimal >= 4.0) {
    const rounded = Math.round((decimal - 1) * 10) / 10;
    // Remove unnecessary .0 (e.g., 20.0 becomes 20)
    const display = rounded % 1 === 0 ? rounded.toFixed(0) : rounded.toFixed(1);
    return `${display}/1`;
  }

  // For lower odds, find the closest common fraction
  let closest = COMMON_FRACTIONS[0];
  let minDiff = Math.abs(decimal - closest.decimal);

  for (const entry of COMMON_FRACTIONS) {
    const diff = Math.abs(decimal - entry.decimal);
    if (diff < minDiff) {
      minDiff = diff;
      closest = entry;
    }
  }

  return closest.fraction;
};

export const formatOdds = (decimalOdds, format = "decimal") => {
  const odds = typeof decimalOdds === "string" ? parseFloat(decimalOdds) : decimalOdds;

  if (isNaN(odds)) return "N/A";

  if (format === "fractional") {
    return decimalToFraction(odds);
  }

  return odds.toFixed(2);
};
