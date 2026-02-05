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

const gcd = (a, b) => {
  return b === 0 ? a : gcd(b, a % b);
};

const decimalToFraction = (decimal) => {
  const fraction = decimal - 1;

  if (fraction === 0) return "EVS";
  if (fraction < 0) return "ERROR";

  const precision = 1000;
  let numerator = Math.round(fraction * precision);
  let denominator = precision;

  const divisor = gcd(numerator, denominator);
  numerator = numerator / divisor;
  denominator = denominator / divisor;

  if (denominator === 1) {
    return `${numerator}/1`;
  }

  return `${numerator}/${denominator}`;
};

export const formatOdds = (decimalOdds, format = "decimal") => {
  const odds = typeof decimalOdds === "string" ? parseFloat(decimalOdds) : decimalOdds;

  if (isNaN(odds)) return "N/A";

  if (format === "fractional") {
    return decimalToFraction(odds);
  }

  return odds.toFixed(2);
};
