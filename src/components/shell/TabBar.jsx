import { Link, useLocation, useParams } from "react-router-dom";
import { groupAcca, groupFixtures, groupTable } from "../../utils/routes";

function IconAcca() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 3h14a1 1 0 0 1 1 1v17l-3.5-2.2L13 21l-3.5-2.2L6 21V4a1 1 0 0 1 1-1Z" />
      <path d="M9 8h6M9 12h6" />
    </svg>
  );
}

function IconFixtures() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </svg>
  );
}

function IconTable() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="13" width="4.5" height="7" rx="1.2" />
      <rect x="9.75" y="5" width="4.5" height="15" rx="1.2" />
      <rect x="16.5" y="10" width="4.5" height="10" rx="1.2" />
    </svg>
  );
}

export default function TabBar() {
  const { groupId } = useParams();
  const { pathname } = useLocation();

  if (!groupId) return null;

  const tabs = [
    // `/acca` prefix also covers the acca detail route at `/accas/:accaId`,
    // so the Acca tab stays lit while you're inside a single acca.
    { to: groupAcca(groupId), match: `/g/${groupId}/acca`, label: "Acca", icon: <IconAcca /> },
    { to: groupFixtures(groupId), match: `/g/${groupId}/fixtures`, label: "Fixtures", icon: <IconFixtures /> },
    { to: groupTable(groupId), match: `/g/${groupId}/table`, label: "Table", icon: <IconTable /> },
  ];

  return (
    <nav className="tab-bar" aria-label="Main">
      <div className="tab-bar-inner">
        {tabs.map(({ to, match, label, icon }) => {
          const active = pathname === match || pathname.startsWith(`${match}/`) || pathname.startsWith(`${match}s/`);
          return (
            <Link
              key={to}
              to={to}
              className={`tab-item${active ? " tab-item-active" : ""}`}
              aria-current={active ? "page" : undefined}
            >
              <span className="tab-icon" aria-hidden="true">{icon}</span>
              <span className="tab-label">{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
