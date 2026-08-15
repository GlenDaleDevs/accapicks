import { Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import AppShell from "./components/shell/AppShell";
import GroupDetail from "./components/GroupDetail";
import AccaDetail from "./components/AccaDetail";
import MemberPickHistory from "./components/MemberPickHistory";
import FixturesTab from "./components/FixturesTab";
import TableTab from "./components/TableTab";
import MoreTab from "./components/MoreTab";
import UserSettings from "./components/UserSettings";
import PageTransition from "./components/PageTransition";
import Skeleton from "./components/Skeleton";
import { useApp } from "./context/AppContext";
import { accaDetail, groupAcca, memberPicks, readLastGroupId } from "./utils/routes";

// Resolves "/" to a group the user is actually still a member of. Validating
// against the fetched list matters on shared devices: a stale lastGroupId from
// a previous user would otherwise 403 on first launch.
function RootRedirect() {
  const { groups, loadingGroups } = useApp();

  if (loadingGroups) {
    return (
      <div className="page-content">
        <Skeleton width="100%" height="80px" count={3} />
      </div>
    );
  }

  // First run: no group to put tabs around yet, so show create/join on its own.
  if (groups.length === 0) return <MoreTab />;

  const stored = readLastGroupId();
  const valid = groups.some((g) => String(g.id) === String(stored));
  return <Navigate to={groupAcca(valid ? stored : groups[0].id)} replace />;
}

// Legacy paths. Settlement push notifications deep-link to
// /groups/{id}/accas/{id} and those payloads are already on users' devices.
function LegacyGroupRedirect() {
  const { groupId } = useParams();
  return <Navigate to={groupAcca(groupId)} replace />;
}

function LegacyMemberRedirect() {
  const { groupId, userId } = useParams();
  return <Navigate to={memberPicks(groupId, userId)} replace />;
}

function LegacyAccaRedirect() {
  const { groupId, accaId } = useParams();
  return <Navigate to={accaDetail(groupId, accaId)} replace />;
}

function SettingsRoute() {
  const { user, oddsFormat, setOddsFormat, onLogout } = useApp();
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate("/");
  };

  return (
    <PageTransition>
      <UserSettings
        user={user}
        oddsFormat={oddsFormat}
        setOddsFormat={setOddsFormat}
        onLogout={handleLogout}
      />
    </PageTransition>
  );
}

export default function AppRoutes() {
  const { user, oddsFormat, bookmakerLinks, onRefreshGroups } = useApp();

  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />

      <Route path="/g/:groupId" element={<AppShell />}>
        <Route index element={<Navigate to="acca" replace />} />
        <Route path="acca" element={<GroupDetail onRefreshGroups={onRefreshGroups} />} />
        <Route
          path="accas/:accaId"
          element={<AccaDetail user={user} oddsFormat={oddsFormat} bookmakerLinks={bookmakerLinks} />}
        />
        <Route path="fixtures" element={<FixturesTab />} />
        <Route path="table" element={<TableTab />} />
        <Route path="more" element={<MoreTab />} />
        <Route path="more/members/:userId" element={<MemberPickHistory user={user} />} />
      </Route>

      <Route path="/settings" element={<SettingsRoute />} />

      <Route path="/groups/:groupId" element={<LegacyGroupRedirect />} />
      <Route path="/groups/:groupId/members/:userId" element={<LegacyMemberRedirect />} />
      <Route path="/groups/:groupId/accas/:accaId" element={<LegacyAccaRedirect />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
