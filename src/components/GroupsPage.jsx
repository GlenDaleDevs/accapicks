import { useNavigate } from "react-router-dom";
import ComplianceFooter from "./ComplianceFooter";
import GroupsList from "./GroupsList";
import { useApp } from "../context/AppContext";

// Create, join and switch groups. Stands on its own now the More tab is gone —
// it is also what a brand new account lands on, before there are tabs to show.
export default function GroupsPage() {
  const { groups, loadingGroups, error, onCreateGroup, onJoinGroup } = useApp();
  const navigate = useNavigate();

  return (
    <div className="groups-page">
      {groups.length > 0 && (
        <button className="settings-back-link" onClick={() => navigate(-1)}>
          ← Back
        </button>
      )}

      <GroupsList
        groups={groups}
        loading={loadingGroups}
        onCreateGroup={onCreateGroup}
        onJoinGroup={onJoinGroup}
        error={error}
      />

      <ComplianceFooter />
    </div>
  );
}
