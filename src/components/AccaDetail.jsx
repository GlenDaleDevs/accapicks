import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { LEAGUE_NAME_MAP } from "../utils/constants";
import { formatCountdown, formatDisplayDate, formatOdds } from "../utils/formatters";
import { showToast } from "../utils/toast";
import * as api from "../api/client";
import FixtureGrid from "./FixtureGrid";
import BookmakerComparison from "./BookmakerComparison";
import BetSlip from "./BetSlip";
import Skeleton from "./Skeleton";

export default function AccaDetail({ user, oddsFormat = "decimal", bookmakerLinks = {} }) {
  const { groupId, accaId } = useParams();
  const navigate = useNavigate();
  const [acca, setAcca] = useState(null);
  const [loadingAcca, setLoadingAcca] = useState(true);
  const [showFixtureGrid, setShowFixtureGrid] = useState(false);
  const [fixtureLeague, setFixtureLeague] = useState("");
  const [filteredMatches, setFilteredMatches] = useState([]);
  const [loadingFilteredMatches, setLoadingFilteredMatches] = useState(false);
  const [showAddBet, setShowAddBet] = useState(false);
  const [matches, setMatches] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [bookmakerComparison, setBookmakerComparison] = useState(null);
  const [comparingBookmakers, setComparingBookmakers] = useState(false);
  const [lockCountdown, setLockCountdown] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (accaId) {
      loadAccaDetails();
    }
  }, [accaId]);

  const loadAccaDetails = async () => {
    setLoadingAcca(true);
    try {
      const data = await api.getAccaById(accaId);
      setAcca(data);
    } catch (err) {
      console.error("Error loading acca details:", err);
      setError(err.response?.data?.detail || "Failed to load acca");
    } finally {
      setLoadingAcca(false);
    }
  };

  // Legacy form state
  const [selectedMatch, setSelectedMatch] = useState("");
  const [betType, setBetType] = useState("home");
  const [customBet, setCustomBet] = useState(false);
  const [betDescription, setBetDescription] = useState("");
  const [betOdds, setBetOdds] = useState("");

  // Lock countdown timer
  useEffect(() => {
    if (!acca || !acca.locks_at || acca.status !== "open") {
      setLockCountdown("");
      return;
    }
    const update = () => setLockCountdown(formatCountdown(acca.locks_at));
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [acca]);

  // Load matches when legacy add bet form opens
  useEffect(() => {
    if (showAddBet && matches.length === 0) {
      loadMatches();
    }
  }, [showAddBet]);

  const loadMatches = async () => {
    setLoadingMatches(true);
    try {
      const data = await api.getMatches();
      setMatches(data);
    } catch (err) {
      console.error("Error loading matches:", err);
      setError("Failed to load matches");
    } finally {
      setLoadingMatches(false);
    }
  };

  const loadFilteredMatches = async (leagues, dates) => {
    setLoadingFilteredMatches(true);
    try {
      const sortedDates = [...dates].sort();
      const data = await api.getFilteredMatches(
        leagues,
        sortedDates[0],
        sortedDates[sortedDates.length - 1],
      );
      setFilteredMatches(data);
    } catch (err) {
      console.error("Error loading filtered matches:", err);
      setError("Failed to load fixtures");
    } finally {
      setLoadingFilteredMatches(false);
    }
  };

  const handleCompareBookmakers = async () => {
    setComparingBookmakers(true);
    setBookmakerComparison(null);
    try {
      const data = await api.compareBookmakers(accaId);
      setBookmakerComparison(data);
    } catch (err) {
      console.error("Error comparing bookmakers:", err);
      setError("Failed to compare bookmakers");
    } finally {
      setComparingBookmakers(false);
    }
  };

  if (loadingAcca) {
    return (
      <div>
        <button
          className="btn btn-ghost mb-20"
          onClick={() => navigate(`/groups/${groupId}`)}
        >
          &larr; Back to Accas
        </button>
        <Skeleton width="250px" height="28px" count={1} />
        <div style={{ marginTop: "20px" }}>
          <Skeleton width="100%" height="100px" count={1} />
        </div>
        <div style={{ marginTop: "20px" }}>
          <Skeleton width="90%" height="80px" count={1} />
          <Skeleton width="85%" height="80px" count={1} />
        </div>
      </div>
    );
  }

  if (error && !acca) {
    return (
      <div>
        <button
          className="btn btn-ghost mb-20"
          onClick={() => navigate(`/groups/${groupId}`)}
        >
          &larr; Back to Accas
        </button>
        <div className="alert-error">{error}</div>
      </div>
    );
  }

  if (!acca) {
    return (
      <div>
        <button
          className="btn btn-ghost mb-20"
          onClick={() => navigate(`/groups/${groupId}`)}
        >
          &larr; Back to Accas
        </button>
        <div className="alert-error">Acca not found</div>
      </div>
    );
  }

  const handlePickFromGrid = async (match, pickType) => {
    setError("");
    let description, odds;
    if (pickType === "home") {
      description = `${match.home_team} to win`;
      odds = String(match.home_odds);
    } else if (pickType === "away") {
      description = `${match.away_team} to win`;
      odds = String(match.away_odds);
    } else {
      description = `Draw - ${match.home_team} vs ${match.away_team}`;
      odds = String(match.draw_odds);
    }

    // Build structured data for auto-settlement
    const structuredData = {
      event_id: match.id,
      home_team: match.home_team,
      away_team: match.away_team,
      pick_type: pickType,
      sport_key: match.league,
      commence_time: match.commence_time,
    };

    try {
      await api.createBet(accaId, description, odds, structuredData);
      loadAccaDetails();
      setShowFixtureGrid(false);
      setFixtureLeague("");
      setFilteredMatches([]);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add pick");
    }
  };

  const handleRemovePick = async (betId) => {
    try {
      await api.deleteBet(betId);
      loadAccaDetails();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to remove pick");
    }
  };

  const handleDeleteAcca = async () => {
    if (!window.confirm("Are you sure? This will delete the acca and all picks.")) {
      return;
    }

    try {
      await api.deleteAcca(accaId);
      showToast("Acca deleted successfully", "success");
      navigate(`/groups/${groupId}`);
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to delete acca", "error");
    }
  };

  // Legacy form helpers
  const getSelectedMatchDetails = () => {
    if (!selectedMatch) return null;
    return matches.find(
      (m) => `${m.home_team}_vs_${m.away_team}` === selectedMatch,
    );
  };

  const getSelectedOdds = () => {
    const match = getSelectedMatchDetails();
    if (!match) return "";
    if (betType === "home") return match.home_odds;
    if (betType === "away") return match.away_odds;
    if (betType === "draw") return match.draw_odds;
    return "";
  };

  const getSelectedDescription = () => {
    const match = getSelectedMatchDetails();
    if (!match) return "";
    if (betType === "home") return `${match.home_team} to win`;
    if (betType === "away") return `${match.away_team} to win`;
    if (betType === "draw") return `Draw - ${match.home_team} vs ${match.away_team}`;
    return "";
  };

  const handleAddBet = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const description = customBet ? betDescription : getSelectedDescription();
      const odds = customBet ? betOdds : String(getSelectedOdds());
      await api.createBet(accaId, description, odds);
      loadAccaDetails();
      setShowAddBet(false);
      setSelectedMatch("");
      setBetType("home");
      setCustomBet(false);
      setBetDescription("");
      setBetOdds("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add bet");
    }
  };

  const userAlreadyPicked = user && acca.bets.some((b) => b.user_id === user.id);
  const canDeleteAcca = user && acca.created_by === user.id && acca.status === "open";

  return (
    <>
      <button
        className="btn btn-ghost mb-20"
        onClick={() => navigate(`/groups/${groupId}`)}
      >
        &larr; Back to Accas
      </button>

    <div className={`page-acca-detail acca-status-${acca?.status || "open"}`}>
      <div style={{ textAlign: "center", marginBottom: "20px" }}>
        <h2 className="section-title" style={{ marginBottom: 0 }}>{acca.name}</h2>
        {canDeleteAcca && (
          <button
            className="btn btn-danger"
            onClick={handleDeleteAcca}
            style={{ fontSize: "14px", padding: "8px 16px", marginTop: "8px" }}
          >
            Delete
          </button>
        )}
      </div>

      {/* Lock countdown / status */}
      {acca.locks_at && acca.status === "open" && (
        <div style={{ textAlign: "center" }}>
          <div className="lock-countdown lock-countdown-open">
            Locks: {lockCountdown}
          </div>
          <p className="bet-settlement-info">
            The acca locks when the earliest picked match kicks off.
          </p>
        </div>
      )}

      {acca.status === "locked" && (
        <div style={{ textAlign: "center" }}>
          <div className="lock-countdown lock-countdown-locked">
            LOCKED - No more picks allowed
          </div>
          <p className="bet-settlement-info">
            This acca locked when the first match kicked off. Results are being tracked automatically.
          </p>
        </div>
      )}

      {/* Bookmaker Comparison - only when open */}
      {acca.status === "open" && (
        <>
          <div className="mb-20">
            <button
              className="btn btn-secondary"
              onClick={handleCompareBookmakers}
              disabled={comparingBookmakers || acca.bets.length === 0}
            >
              {comparingBookmakers ? "Comparing..." : "Compare Bookmakers"}
            </button>
          </div>

          <BookmakerComparison data={bookmakerComparison} oddsFormat={oddsFormat} bookmakerLinks={bookmakerLinks} accaId={accaId} />
        </>
      )}

      {/* Add Pick - Fixture Grid Flow */}
      {acca.status === "open" && !showFixtureGrid && !showAddBet && (
        <div className="mb-20 btn-group">
          <button
            className={`btn ${userAlreadyPicked ? "btn-secondary" : "btn-primary"}`}
            disabled={userAlreadyPicked}
            onClick={() => {
              if (
                acca.leagues &&
                acca.leagues.length > 0 &&
                acca.match_dates &&
                acca.match_dates.length > 0
              ) {
                if (acca.leagues.length === 1) {
                  setFixtureLeague(acca.leagues[0]);
                  loadFilteredMatches(acca.leagues, acca.match_dates);
                }
                setShowFixtureGrid(true);
              } else {
                setShowAddBet(true);
              }
            }}
          >
            {userAlreadyPicked ? "Pick Already Submitted" : "+ Add Your Pick"}
          </button>
        </div>
      )}

      {/* Fixture Grid */}
      {showFixtureGrid && (
        <FixtureGrid
          acca={acca}
          filteredMatches={filteredMatches}
          loadingFilteredMatches={loadingFilteredMatches}
          fixtureLeague={fixtureLeague}
          onPickMatch={handlePickFromGrid}
          onSelectLeague={(key) => {
            setFixtureLeague(key);
            loadFilteredMatches([key], acca.match_dates);
          }}
          onCancel={() => {
            setShowFixtureGrid(false);
            setFixtureLeague("");
            setFilteredMatches([]);
            setError("");
          }}
          error={error}
          oddsFormat={oddsFormat}
        />
      )}

      {/* Legacy add bet form */}
      {showAddBet && (
        <div className="form-panel">
          <h3 className="form-panel-title">Add Your Bet</h3>

          {error && <div className="alert-error">{error}</div>}

          <label className="custom-bet-toggle">
            <input
              type="checkbox"
              checked={customBet}
              onChange={(e) => setCustomBet(e.target.checked)}
            />
            Enter custom bet (not from live matches)
          </label>

          {!customBet ? (
            <form onSubmit={handleAddBet}>
              {loadingMatches ? (
                <p className="text-secondary">Loading matches...</p>
              ) : (
                <>
                  <div className="form-group">
                    <label className="section-subtitle">Select Match:</label>
                    <select
                      value={selectedMatch}
                      onChange={(e) => setSelectedMatch(e.target.value)}
                      required
                    >
                      <option value="">-- Choose a match --</option>
                      {matches.map((match, idx) => (
                        <option
                          key={idx}
                          value={`${match.home_team}_vs_${match.away_team}`}
                        >
                          {match.home_team} vs {match.away_team} -{" "}
                          {new Date(match.commence_time).toLocaleDateString()}
                        </option>
                      ))}
                    </select>
                  </div>

                  {selectedMatch && (
                    <div className="form-group">
                      <label className="section-subtitle">Select Bet:</label>
                      <select
                        value={betType}
                        onChange={(e) => setBetType(e.target.value)}
                        required
                      >
                        <option value="home">
                          {getSelectedMatchDetails()?.home_team} to win (Odds:{" "}
                          {getSelectedMatchDetails()?.home_odds})
                        </option>
                        <option value="draw">
                          Draw (Odds: {getSelectedMatchDetails()?.draw_odds})
                        </option>
                        <option value="away">
                          {getSelectedMatchDetails()?.away_team} to win (Odds:{" "}
                          {getSelectedMatchDetails()?.away_odds})
                        </option>
                      </select>
                    </div>
                  )}

                  {selectedMatch && (
                    <div className="bet-preview">
                      <p className="bet-preview-desc">
                        <strong>Your Bet:</strong> {getSelectedDescription()}
                      </p>
                      <p className="bet-preview-odds">
                        Odds: {getSelectedOdds()}
                      </p>
                      <p className="bet-preview-source">
                        Source: {getSelectedMatchDetails()?.bookmaker}
                      </p>
                    </div>
                  )}
                </>
              )}

              <div className="btn-group">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!selectedMatch || loadingMatches}
                >
                  Add Bet
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setShowAddBet(false);
                    setSelectedMatch("");
                    setBetType("home");
                    setCustomBet(false);
                    setError("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleAddBet}>
              <div className="form-group">
                <input
                  type="text"
                  placeholder="Bet Description (e.g., Liverpool to win)"
                  value={betDescription}
                  onChange={(e) => setBetDescription(e.target.value)}
                  required
                  maxLength={200}
                />
              </div>

              <div className="form-group">
                <input
                  type="text"
                  placeholder="Odds (e.g., 2.5)"
                  value={betOdds}
                  onChange={(e) => setBetOdds(e.target.value)}
                  required
                  maxLength={20}
                />
              </div>

              <div className="btn-group">
                <button type="submit" className="btn btn-primary">
                  Add Bet
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setShowAddBet(false);
                    setBetDescription("");
                    setBetOdds("");
                    setCustomBet(false);
                    setError("");
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      <BetSlip
        acca={acca}
        oddsFormat={oddsFormat}
        bookmakerComparison={bookmakerComparison}
        bookmakerLinks={bookmakerLinks}
      />
    </div>
    </>
  );
}
