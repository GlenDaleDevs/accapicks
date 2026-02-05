import { getDaysInMonth, getFirstDayOfMonth, formatDateStr, isDateInPast } from "../utils/formatters";

export default function Calendar({ selectedDates, maxDates, currentMonth, onToggleDate, onMonthChange }) {
  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);
  const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const monthName = currentMonth.toLocaleDateString("en-GB", {
    month: "long",
    year: "numeric",
  });

  const cells = [];
  for (let i = 0; i < firstDay; i++) {
    cells.push(<div key={`empty-${i}`} />);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = formatDateStr(year, month, day);
    const isPast = isDateInPast(dateStr);
    const isSelected = selectedDates.includes(dateStr);
    cells.push(
      <div
        key={dateStr}
        onClick={() => !isPast && onToggleDate(dateStr)}
        className={`calendar-day${isPast ? " calendar-day-past" : ""}${isSelected ? " calendar-day-selected" : ""}`}
      >
        {day}
      </div>,
    );
  }

  return (
    <div>
      <div className="calendar-nav">
        <button
          type="button"
          className="btn btn-ghost btn-icon"
          onClick={() => onMonthChange(new Date(year, month - 1, 1))}
        >
          &lt;
        </button>
        <strong className="calendar-month-label">{monthName}</strong>
        <button
          type="button"
          className="btn btn-ghost btn-icon"
          onClick={() => onMonthChange(new Date(year, month + 1, 1))}
        >
          &gt;
        </button>
      </div>
      <div className="calendar-grid">
        {dayNames.map((d) => (
          <div key={d} className="calendar-dayname">
            {d}
          </div>
        ))}
        {cells}
      </div>
      <p className="calendar-info">
        Selected: {selectedDates.length} of {maxDates} dates
        {selectedDates.length > 0 && (
          <span>
            {" "}
            ({[...selectedDates].sort().map((d) => {
              const dt = new Date(d + "T00:00:00");
              return dt.toLocaleDateString("en-GB", { month: "short", day: "numeric" });
            }).join(", ")})
          </span>
        )}
      </p>
    </div>
  );
}
