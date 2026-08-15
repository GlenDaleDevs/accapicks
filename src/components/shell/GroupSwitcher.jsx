import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { groupAcca, groupMore, writeLastGroupId } from "../../utils/routes";

export default function GroupSwitcher() {
  const { groups } = useApp();
  const { groupId } = useParams();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  const current = groups.find((g) => String(g.id) === String(groupId));

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    const onKeyDown = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  // Switching group always resets to that group's Acca tab.
  const selectGroup = (id) => {
    writeLastGroupId(id);
    setOpen(false);
    navigate(groupAcca(id));
  };

  return (
    <div className="group-switcher" ref={wrapRef}>
      <button
        type="button"
        className="group-switcher-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span className="group-switcher-name">{current?.name || "Select group"}</span>
        <svg className="group-switcher-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {open && (
        <div className="group-switcher-menu" role="menu">
          {groups.map((g) => {
            const active = String(g.id) === String(groupId);
            return (
              <button
                key={g.id}
                type="button"
                role="menuitem"
                className={`group-switcher-item${active ? " group-switcher-item-active" : ""}`}
                onClick={() => selectGroup(g.id)}
              >
                <span className="group-switcher-item-name">{g.name}</span>
                {active && <span className="group-switcher-check" aria-hidden="true">✓</span>}
              </button>
            );
          })}
          <button
            type="button"
            role="menuitem"
            className="group-switcher-item group-switcher-manage"
            onClick={() => {
              setOpen(false);
              navigate(groupMore(groupId));
            }}
          >
            Manage groups
          </button>
        </div>
      )}
    </div>
  );
}
