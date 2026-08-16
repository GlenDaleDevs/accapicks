import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as api from "../api/client";
import { showToast } from "../utils/toast";
import { useApp } from "../context/AppContext";
import { ACCA_STATE, getAccaState, isExpired } from "../utils/accaState";
import { buildPick, buildStructuredData } from "../utils/pickDescription";
import { groupAcca } from "../utils/routes";
import WeekStrip from "./acca/WeekStrip";
import AccaBody from "./acca/AccaBody";
import Modal from "./ui/Modal";
import FixtureGrid from "./FixtureGrid";
import AccaWizard from "./AccaWizard";
import Skeleton from "./Skeleton";
import "./acca/acca.css";

// Resolution order: the soonest week still taking picks, else the one in play,
// else the most recent result. The list arrives sorted by first_match_date —
// locks_at can't be used here because it stays null until somebody picks, so
// several open weeks would share a null lock time.
function resolveCurrent(accas) {
  if (accas.length === 0) return null;
  // Earliest open week that hasn't expired: that's the deadline approaching.
  // Expired ones must be skipped — an acca nobody picked in stays "open"
  // forever, and landing on one offers picks that can never be made.
  const live = accas.find((a) => a.status === "open" && !isExpired(a));
  if (live) return live;
  const locked = accas.filter((a) => a.status === "locked");
  if (locked.length) return locked[locked.length - 1];
  const settled = accas.filter((a) => ["won", "lost", "settled"].includes(a.status));
  if (settled.length) return settled[settled.length - 1];
  return accas[accas.length - 1];
}

export default function AccaTab({ user, oddsFormat }) {
  const { groupId, roundNumber } = useParams();
  const navigate = useNavigate();
  const { groups } = useApp();
  const autoWeeks = groups.find((g) => String(g.id) === String(groupId))?.auto_weeks;

  const [accas, setAccas] = useState([]);
  const [members, setMembers] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showWizard, setShowWizard] = useState(false);
  const [showPicker, setShowPicker] = useState(false);
  const [fixtureLeague, setFixtureLeague] = useState("");
  const [matches, setMatches] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const detailIdRef = useRef(null);

  const loadIndex = useCallback(async () => {
    try {
      const [accaList, memberList] = await Promise.all([
        api.getAccasByGroup(groupId),
        api.getGroupMembers(groupId),
      ]);
      setAccas(accaList);
      setMembers(memberList);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load group");
    } finally {
      setLoading(false);
    }
  }, [groupId]);

  useEffect(() => {
    setLoading(true);
    loadIndex();
  }, [loadIndex]);

  const current = useMemo(() => resolveCurrent(accas), [accas]);
  const selected = useMemo(() => {
    if (!roundNumber) return current;
    return accas.find((a) => String(a.round_number) === String(roundNumber)) || current;
  }, [accas, roundNumber, current]);

  const selectedIndex = selected ? accas.findIndex((a) => a.id === selected.id) : -1;
  const isCurrent = selected && current && selected.id === current.id;

  const loadDetail = useCallback(async (accaId, showSpinner) => {
    if (!accaId) return;
    if (showSpinner) setDetail(null);
    try {
      const data = await api.getAccaById(accaId);
      setDetail(data);
    } catch (err) {
      // A week can vanish: accas with under 50% participation are deleted at
      // lock time, so a bookmarked or notified link can outlive its acca.
      if (err.response?.status === 404 || err.response?.status === 403) {
        showToast("That week is no longer available", "info");
        navigate(groupAcca(groupId), { replace: true });
      }
    }
  }, [groupId, navigate]);

  useEffect(() => {
    if (!selected) return;
    const changed = detailIdRef.current !== selected.id;
    detailIdRef.current = selected.id;
    loadDetail(selected.id, changed);
  }, [selected, loadDetail]);

  const state = useMemo(() => getAccaState(detail, members), [detail, members]);

  // Open accas change as mates pick; in-play accas change as results land.
  // Previously only open accas polled, so live results never arrived.
  useEffect(() => {
    if (!detail) return;
    if (state !== ACCA_STATE.OPEN && state !== ACCA_STATE.IN_PLAY) return;
    const interval = state === ACCA_STATE.OPEN ? 30000 : 60000;
    const id = setInterval(() => {
      loadDetail(detail.id, false);
      loadIndex();
    }, interval);
    return () => clearInterval(id);
  }, [detail, state, loadDetail, loadIndex]);

  const goToWeek = (acca) => navigate(`/g/${groupId}/acca/${acca.round_number}`);

  const openPicker = async () => {
    setShowPicker(true);
    const leagues = detail?.leagues || [];
    if (leagues.length === 1) {
      setFixtureLeague(leagues[0]);
      await loadMatches(leagues[0]);
    }
  };

  const loadMatches = async (league) => {
    if (!detail?.match_dates?.length) return;
    const sorted = [...detail.match_dates].sort();
    setLoadingMatches(true);
    try {
      const data = await api.getFilteredMatches([league], sorted[0], sorted[sorted.length - 1]);
      setMatches(data);
    } catch {
      setMatches([]);
    } finally {
      setLoadingMatches(false);
    }
  };

  const handlePick = async (match, pickType) => {
    if (submitting) return;
    const built = buildPick(match, pickType);
    if (!built) return;
    setSubmitting(true);
    try {
      await api.createBet(detail.id, built.description, built.odds, buildStructuredData(match, pickType));
      await loadDetail(detail.id, false);
      await loadIndex();
      setShowPicker(false);
      setMatches([]);
      setFixtureLeague("");
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to add pick", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async (betId) => {
    if (!window.confirm("Remove this pick?")) return;
    try {
      await api.deleteBet(betId);
      await loadDetail(detail.id, false);
      await loadIndex();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to remove pick", "error");
    }
  };

  const handleDelete = async () => {
    if (!detail) return;
    const label = detail.week_number ? `Week ${detail.week_number}` : "this week";
    const picks = (detail.bets || []).length;
    const warning = picks
      ? `Delete ${label}? ${picks} pick${picks === 1 ? "" : "s"} will go with it.`
      : `Delete ${label}?`;
    if (!window.confirm(warning)) return;
    setDeleting(true);
    try {
      await api.deleteAcca(detail.id);
      showToast("Week deleted", "success");
      navigate(groupAcca(groupId), { replace: true });
      await loadIndex();
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to delete week", "error");
    } finally {
      setDeleting(false);
    }
  };

  const handleCreate = async ({ name, matchDates, leagues, betType }) => {
    try {
      const created = await api.createAcca(groupId, name, matchDates, leagues, betType);
      setShowWizard(false);
      await loadIndex();
      navigate(`/g/${groupId}/acca/${created.round_number}`);
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to create week", "error");
    }
  };

  if (loading) {
    return (
      <div className="acca-tab page-content">
        <Skeleton width="60%" height="28px" count={1} />
        <div className="skeleton-spacer">
          <Skeleton width="100%" height="120px" count={1} />
        </div>
      </div>
    );
  }

  if (error) {
    return <div className="acca-tab page-content"><div className="alert-error">{error}</div></div>;
  }

  if (!selected) {
    return (
      <div className="acca-tab">
        <div className="placeholder-card">
          <h3 className="placeholder-title">No weeks yet</h3>
          <p className="placeholder-text">Start one and your mates can add their picks.</p>
          <button className="btn btn-primary mt-16" onClick={() => setShowWizard(true)}>
            Create the first week
          </button>
        </div>
        <Modal open={showWizard} title="New week" onClose={() => setShowWizard(false)}>
          <AccaWizard onCreated={handleCreate} onCancel={() => setShowWizard(false)} />
        </Modal>
      </div>
    );
  }

  // Settled weeks are the read-only ones. A *later* open week is still
  // pickable, so "not current" alone must not lock the UI.
  const readOnly = state === ACCA_STATE.SETTLED || state === ACCA_STATE.EXPIRED;
  const currentIndex = current ? accas.findIndex((a) => a.id === current.id) : -1;
  const hasLiveWeek = accas.some((a) => a.status === "open" && !isExpired(a));

  // Deleting is only possible while a week is still open — once it locks, the
  // backend refuses. Auto-created weeks have no creator, so for those it's the
  // group admin or nobody.
  const isGroupAdmin = members.some((m) => m.user_id === user?.id && m.role === "admin");
  const canDelete = detail?.status === "open" && (isGroupAdmin || detail?.created_by === user?.id);
  // Season-relative, matching the label the week will actually get. Counting
  // round_number here would offer "Start week 34" in a group's third season.
  const nextWeekNumber = accas.reduce((max, a) => Math.max(max, a.week_number || 0), 0) + 1;

  return (
    <div className="acca-tab">
      <WeekStrip
        acca={detail || selected}
        state={state}
        hasPrev={selectedIndex > 0}
        hasNext={selectedIndex >= 0 && selectedIndex < accas.length - 1}
        onPrev={() => goToWeek(accas[selectedIndex - 1])}
        onNext={() => goToWeek(accas[selectedIndex + 1])}
        showBackToCurrent={!isCurrent && Math.abs(currentIndex - selectedIndex) > 1}
        onBackToCurrent={() => navigate(groupAcca(groupId))}
      />

      {readOnly && (
        <div className="week-readonly-note">
          {state === ACCA_STATE.EXPIRED ? "Lapsed — no picks were made" : "Settled — read only"}
        </div>
      )}

      {/* When there's no week left to pick for, starting one IS the task —
          it shouldn't be a small ghost button under everything else. Unless
          weeks open by themselves, in which case waiting is the right move and
          the manual route steps back to being the exception. */}
      {!hasLiveWeek && (
        <div className="new-week-card">
          <h3 className="new-week-title">
            {autoWeeks
              ? "Next week isn't open yet"
              : state === ACCA_STATE.EXPIRED ? "This week never got going" : "No week open"}
          </h3>
          <p className="new-week-text">
            {autoWeeks
              ? "It opens a few days before the next Saturday's fixtures. Start one yourself if you can't wait."
              : state === ACCA_STATE.EXPIRED
                ? "Nobody picked, so it lapsed. Start the next one to get going."
                : "Start the next week and your mates can add their picks."}
          </p>
          <button
            className={`btn ${autoWeeks ? "btn-ghost" : "btn-primary"}`}
            onClick={() => setShowWizard(true)}
          >
            Start week {nextWeekNumber}
          </button>
        </div>
      )}

      {detail ? (
        <AccaBody
          acca={detail}
          state={state}
          members={members}
          user={user}
          oddsFormat={oddsFormat}
          onAddPick={openPicker}
          onRemovePick={handleRemove}
          readOnly={readOnly}
        />
      ) : (
        <div className="page-content"><Skeleton width="100%" height="120px" count={1} /></div>
      )}

      {(canDelete || (isCurrent && hasLiveWeek)) && (
        <div className="acca-tab-actions">
          {isCurrent && hasLiveWeek && (
            <button className="btn btn-ghost" onClick={() => setShowWizard(true)}>
              + New week
            </button>
          )}
          {canDelete && (
            <button className="acca-delete-link" onClick={handleDelete} disabled={deleting}>
              {deleting ? "Deleting…" : "Delete this week"}
            </button>
          )}
        </div>
      )}

      <Modal open={showPicker} title="Pick a match" onClose={() => setShowPicker(false)}>
        {detail && (
          <FixtureGrid
            acca={detail}
            filteredMatches={matches}
            loadingFilteredMatches={loadingMatches}
            fixtureLeague={fixtureLeague}
            onSelectLeague={(l) => { setFixtureLeague(l); loadMatches(l); }}
            onPickMatch={handlePick}
            onCancel={() => setShowPicker(false)}
            oddsFormat={oddsFormat}
            isSubmitting={submitting}
          />
        )}
      </Modal>

      <Modal open={showWizard} title="New week" onClose={() => setShowWizard(false)}>
        <AccaWizard onCreated={handleCreate} onCancel={() => setShowWizard(false)} />
      </Modal>
    </div>
  );
}
