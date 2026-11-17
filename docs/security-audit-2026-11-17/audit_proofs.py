"""Audit proofs for AccaPicks, run against commit 29d41e8 (see README.md).

Throwaway local database only: the first thing each test does is DROP and recreate every table, so
NEVER point DATABASE_URL at the live database. Each test asserts the behaviour found at audit time:
for a gap, passing means "gap still present"; once a gap is fixed its proof is expected to fail.
The file name does not match test_*.py and it lives outside backend/tests, so CI never collects it.
"""
import asyncio, base64, logging, os, socket, subprocess, sys, threading, time
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest

_db_url = os.environ.get("DATABASE_URL", "")
if not any(h in _db_url for h in ("@127.0.0.1", "@localhost", "sqlite")):
    pytest.exit("audit_proofs.py drops every table: set DATABASE_URL to a throwaway LOCAL database")
from fastapi.testclient import TestClient

from app import main, models, odds_api, settlement
from app.database import Base, engine, SessionLocal
from app.limiter import limiter
from app.routers import auth as auth_router

limiter.enabled = False
CODES = {}


def _capture(to, code, username):
    CODES[to.lower()] = code


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    odds_api._cache.clear()
    monkeypatch.setattr(auth_router, "send_verification_email", _capture)
    monkeypatch.setattr(auth_router, "send_password_reset_email", _capture)
    yield


@pytest.fixture
def c():
    return TestClient(main.app, raise_server_exceptions=False)


def _vapid_keys():
    """A throwaway signing key pair made at run time (nothing secret is stored in this file)."""
    from cryptography.hazmat.primitives import serialization
    from py_vapid import Vapid
    v = Vapid(); v.generate_keys()
    b64 = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("=")
    priv = b64(v.private_key.private_numbers().private_value.to_bytes(32, "big"))
    pub = b64(v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
    return priv, pub


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


def user(c, email, name, pw="password1"):
    assert c.post("/api/auth/signup", json={"email": email, "username": name, "password": pw, "age_confirmed": True}).status_code == 201
    r = c.post("/api/auth/verify-email", json={"email": email, "code": CODES[email]})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def login(c, ident, pw="password1"):
    return c.post("/api/auth/login", json={"identifier": ident, "password": pw})


def group(c, tok, name="G"):
    r = c.post("/api/groups", json={"name": name}, headers=H(tok))
    return r.json()


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def acca(c, tok, gid, dates=None):
    r = c.post("/api/accas", json={"group_id": gid, "name": "Wk", "match_dates": dates or [today()], "leagues": ["soccer_epl"]}, headers=H(tok))
    assert r.status_code == 201, r.text
    return r.json()


def seed_match(event_id, kickoff):
    odds_api._cache["soccer_epl"] = {"timestamp": time.time(), "data": [{
        "id": event_id, "home_team": "Arsenal", "away_team": "Chelsea", "commence_time": kickoff.isoformat(),
        "bookmakers": [{"title": "Unibet", "markets": [{"key": "h2h", "outcomes": [
            {"name": "Arsenal", "price": 1.5}, {"name": "Chelsea", "price": 6.0}, {"name": "Draw", "price": 4.0}]}]}]}]}


# ---------------- Sign-in and sessions ----------------

def test_change_password_leaves_other_devices_signed_in(c):
    phone = user(c, "a@x.com", "alice")
    laptop = login(c, "alice").json()["access_token"]
    assert c.put("/api/auth/change-password", json={"current_password": "password1", "new_password": "newpass99"}, headers=H(laptop)).status_code == 200
    r = c.get("/api/auth/me", headers=H(phone))
    print("\nPROOF other device after password change ->", r.status_code)
    assert r.status_code == 200


def test_reset_password_ends_no_sessions(c):
    stolen = user(c, "a@x.com", "alice")
    c.post("/api/auth/forgot-password", json={"email": "a@x.com"})
    assert c.post("/api/auth/reset-password", json={"email": "a@x.com", "code": CODES["a@x.com"], "new_password": "brandnew9"}).status_code == 200
    r = c.get("/api/auth/me", headers=H(stolen))
    print("\nPROOF old token after password RESET ->", r.status_code)
    assert r.status_code == 200


def test_deleted_account_token_still_accepted(c):
    tok = user(c, "a@x.com", "alice")
    assert c.post("/api/auth/delete-account", json={"password": "password1"}, headers=H(tok)).status_code == 200
    r = c.get("/api/groups", headers=H(tok))
    print("\nPROOF deleted account's token on /groups ->", r.status_code, r.text)
    assert r.status_code == 200


def test_login_locked_answer_differs_from_unknown(c):
    user(c, "a@x.com", "alice")
    unknown = login(c, "nobody", "wrong")
    for _ in range(10):
        login(c, "alice", "wrongpass")
    locked = login(c, "alice", "wrongpass")
    print("\nPROOF unknown:", unknown.status_code, unknown.json(), "| locked:", locked.status_code, locked.json())
    assert unknown.status_code == 401 and locked.status_code == 403


def test_forgot_password_reveals_accounts(c, monkeypatch):
    user(c, "a@x.com", "alice")
    from app import email as email_mod
    monkeypatch.setattr(auth_router, "send_password_reset_email", email_mod.send_password_reset_email)  # real one; no RESEND key -> raises
    real = c.post("/api/auth/forgot-password", json={"email": "a@x.com"})
    fake = c.post("/api/auth/forgot-password", json={"email": "nobody@x.com"})
    print("\nPROOF forgot-password real:", real.status_code, "| unknown:", fake.status_code)
    assert real.status_code == 500 and fake.status_code == 200
    # timing: a slow (but working) email provider shows up only for real accounts
    monkeypatch.setattr(auth_router, "send_password_reset_email", lambda *a: time.sleep(0.4))
    t = time.perf_counter(); c.post("/api/auth/forgot-password", json={"email": "a@x.com"}); real_t = time.perf_counter() - t
    t = time.perf_counter(); c.post("/api/auth/forgot-password", json={"email": "nobody@x.com"}); fake_t = time.perf_counter() - t
    print(f"PROOF forgot-password timing real={real_t:.2f}s unknown={fake_t:.2f}s")
    assert real_t > fake_t + 0.3


def test_reset_password_reveals_accounts(c):
    user(c, "a@x.com", "alice")
    known = c.post("/api/auth/reset-password", json={"email": "a@x.com", "code": "123456", "new_password": "brandnew9"})
    unknown = c.post("/api/auth/reset-password", json={"email": "nobody@x.com", "code": "123456", "new_password": "brandnew9"})
    print("\nPROOF reset known:", known.json(), "| unknown:", unknown.json())
    assert known.json() != unknown.json()


def test_non_ascii_code_is_server_error(c):
    c.post("/api/auth/signup", json={"email": "a@x.com", "username": "alice", "password": "password1", "age_confirmed": True})
    r = c.post("/api/auth/verify-email", json={"email": "a@x.com", "code": "ééééé1"})
    print("\nPROOF non-ASCII code ->", r.status_code)
    assert r.status_code == 500


def test_legacy_bcrypt_long_password_is_server_error(c):
    db = SessionLocal()
    db.add(models.User(email="old@x.com", username="olduser", email_verified=True,
                       hashed_password=bcrypt.hashpw(b"password1", bcrypt.gensalt()).decode()))
    db.commit(); db.close()
    r = login(c, "olduser", "a" * 100)
    print("\nPROOF legacy bcrypt user, 100-char password ->", r.status_code)
    assert r.status_code == 500


def test_placeholder_secret_key_accepted():
    env = dict(os.environ, SECRET_KEY="generate-with-python-c-import-secrets-print-secrets-token-hex-32")
    r = subprocess.run([sys.executable, "-c", "import app.auth as a; print('started with', len(a.SECRET_KEY), 'char placeholder')"], env=env, capture_output=True, text=True)
    env["SECRET_KEY"] = "x"
    r2 = subprocess.run([sys.executable, "-c", "import app.auth; print('started with 1-char key')"], env=env, capture_output=True, text=True)
    print("\nPROOF", r.stdout.strip(), "|", r2.stdout.strip())
    assert r.returncode == 0 and r2.returncode == 0


def test_unlimited_codes_and_guesses(c):
    c.post("/api/auth/signup", json={"email": "a@x.com", "username": "alice", "password": "password1", "age_confirmed": True})
    guesses = 0
    for _ in range(4):  # four rounds: 5 wrong guesses, then a fresh code
        for g in range(6):
            r = c.post("/api/auth/verify-email", json={"email": "a@x.com", "code": "000000"})
            if "Invalid verification code" in r.text:
                guesses += 1
        assert c.post("/api/auth/resend-code", json={"email": "a@x.com"}).status_code == 200
    sends = [c.post("/api/auth/resend-code", json={"email": "a@x.com"}).status_code for _ in range(30)]
    print(f"\nPROOF {guesses} wrong guesses accepted across 4 codes; 30 back-to-back resends ->", set(sends))
    assert guesses > 5 and set(sends) == {200}


def test_pending_signup_takeover(c):
    c.post("/api/auth/signup", json={"email": "v@x.com", "username": "victim", "password": "victimpw1", "age_confirmed": True})
    c.post("/api/auth/signup", json={"email": "v@x.com", "username": "attacker", "password": "attackpw1", "age_confirmed": True})
    # The victim types the code from THEIR inbox into the app (email + code only)
    r = c.post("/api/auth/verify-email", json={"email": "v@x.com", "code": CODES["v@x.com"]})
    who = r.json()["user"]["username"]
    att = login(c, "v@x.com", "attackpw1")
    print("\nPROOF victim's code verified account:", who, "| attacker's password logs in:", att.status_code)
    assert who == "attacker" and att.status_code == 200


def test_login_logs_full_email(c, caplog):
    user(c, "alice.smith@example.com", "alice")
    with caplog.at_level(logging.WARNING):
        login(c, "alice.smith@example.com", "wrongpass")
    print("\nPROOF log line:", [r.getMessage() for r in caplog.records if "Failed login" in r.getMessage()])
    assert any("alice.smith@example.com" in r.getMessage() for r in caplog.records)


# ---------------- Who can see what ----------------

def test_cross_group_isolation(c):
    a = user(c, "a@x.com", "alice"); b = user(c, "b@x.com", "bob")
    ga = group(c, a, "A"); gb = group(c, b, "B")
    acb = acca(c, b, gb["id"])
    bob_id = c.get("/api/auth/me", headers=H(b)).json()["id"]
    probes = {
        "GET group": c.get(f"/api/groups/{gb['id']}", headers=H(a)),
        "GET accas": c.get(f"/api/groups/{gb['id']}/accas", headers=H(a)),
        "GET acca": c.get(f"/api/accas/{acb['id']}", headers=H(a)),
        "GET members": c.get(f"/api/groups/{gb['id']}/members", headers=H(a)),
        "GET leaderboard": c.get(f"/api/groups/{gb['id']}/leaderboard", headers=H(a)),
        "GET acca-stats": c.get(f"/api/groups/{gb['id']}/acca-stats", headers=H(a)),
        "GET picks": c.get(f"/api/groups/{gb['id']}/members/{bob_id}/picks", headers=H(a)),
        "PATCH group": c.patch(f"/api/groups/{gb['id']}", json={"name": "pwn"}, headers=H(a)),
        "POST acca in B": c.post("/api/accas", json={"group_id": gb["id"], "name": "x", "match_dates": [today()], "leagues": ["soccer_epl"]}, headers=H(a)),
        "POST bet in B": c.post("/api/bets", json={"acca_id": acb["id"], "description": "x", "odds": "2"}, headers=H(a)),
        "DELETE acca": c.delete(f"/api/accas/{acb['id']}", headers=H(a)),
        "nudge": c.post(f"/api/accas/{acb['id']}/nudge/{bob_id}", headers=H(a)),
        "remove member": c.delete(f"/api/groups/{gb['id']}/members/{bob_id}", headers=H(a)),
        "transfer admin": c.post(f"/api/groups/{gb['id']}/transfer-admin", json={"new_admin_id": bob_id}, headers=H(a)),
        "device token": c.post(f"/api/groups/{gb['id']}/device-token", headers=H(a)),
        "compare": c.get(f"/api/accas/{acb['id']}/compare-bookmakers", headers=H(a)),
    }
    missing = {"GET group": c.get("/api/groups/999999", headers=H(a)), "GET acca": c.get("/api/accas/999999", headers=H(a))}
    print("\nPROOF cross-group:", {k: v.status_code for k, v in probes.items()})
    print("PROOF missing ids:", {k: v.status_code for k, v in missing.items()})
    assert all(v.status_code in (403,) for v in probes.values())
    assert c.get(f"/api/groups/{gb['id']}", headers=H(b)).json()["name"] == "B"  # unchanged


def test_odd_ids(c):
    a = user(c, "a@x.com", "alice")
    out = {}
    for v in ["0", "-1", "2147483648", "9223372036854775808", "99999999999999999999", "abc"]:
        out[v] = (c.get(f"/api/groups/{v}", headers=H(a)).status_code, c.get(f"/api/accas/{v}", headers=H(a)).status_code,
                  c.delete(f"/api/bets/{v}", headers=H(a)).status_code)
    print("\nCHECK odd ids (group, acca, bet):", out)
    # Passed at audit time on PostgreSQL: always a clean 404/422, never a 500
    assert not any(500 in t for t in out.values())


def test_removed_member_can_rejoin_with_same_code(c):
    a = user(c, "a@x.com", "alice"); m = user(c, "m@x.com", "mallory")
    g = group(c, a)
    c.post(f"/api/groups/join/{g['invite_code']}", headers=H(m))
    mid = c.get("/api/auth/me", headers=H(m)).json()["id"]
    assert c.delete(f"/api/groups/{g['id']}/members/{mid}", headers=H(a)).status_code == 200
    r = c.post(f"/api/groups/join/{g['invite_code']}", headers=H(m))
    print("\nPROOF removed member rejoins with old code ->", r.status_code, r.json())
    assert r.status_code == 200


# ---------------- Picks / fair play ----------------

def test_pick_after_kickoff_with_forged_time_and_it_wins(c, monkeypatch):
    a = user(c, "a@x.com", "alice")
    g = group(c, a)
    ac = acca(c, a, g["id"])
    real_kickoff = datetime.now(timezone.utc) - timedelta(minutes=100)  # match nearly over
    seed_match("evt1", real_kickoff)
    fake = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    r = c.post("/api/bets", json={"acca_id": ac["id"], "description": "x", "odds": "1", "event_id": "evt1",
                                  "pick_type": "home", "sport_key": "soccer_epl", "commence_time": fake}, headers=H(a))
    print("\nPROOF pick on match that kicked off 100 min ago ->", r.status_code, "stored kickoff:", r.json().get("commence_time"))
    assert r.status_code == 201
    d = c.delete(f"/api/bets/{r.json()['id']}", headers=H(a))
    print("PROOF delete pick after real kickoff ->", d.status_code)
    assert d.status_code == 200
    r = c.post("/api/bets", json={"acca_id": ac["id"], "description": "x", "odds": "1", "event_id": "evt1",
                                  "pick_type": "home", "sport_key": "soccer_epl", "commence_time": fake}, headers=H(a))
    # settlement keys on event_id; the real final score comes back as a home win
    db = SessionLocal(); db.query(models.Acca).filter_by(id=ac["id"]).update({"status": "locked"}); db.commit()
    later = datetime.now(timezone.utc) + timedelta(days=3, hours=3)

    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return later
    monkeypatch.setattr(settlement, "datetime", Later)
    monkeypatch.setattr(settlement, "get_scores", lambda *a, **k: [{"id": "evt1", "completed": True, "scores": [
        {"name": "Arsenal", "score": "2"}, {"name": "Chelsea", "score": "0"}]}])
    settlement.settle_locked_accas(db)
    res = db.query(models.Bet).filter_by(acca_id=ac["id"]).one().result
    print("PROOF settled result of the late pick ->", res); db.close()
    assert res == "won"


def test_forged_time_locks_week_early(c):
    a = user(c, "a@x.com", "alice")
    g = group(c, a)
    ac = acca(c, a, g["id"], dates=[(datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")])
    seed_match("evt2", datetime.now(timezone.utc) + timedelta(days=2))
    soon = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    c.post("/api/bets", json={"acca_id": ac["id"], "description": "x", "odds": "1", "event_id": "evt2",
                              "pick_type": "home", "sport_key": "soccer_epl", "commence_time": soon}, headers=H(a))
    locks = c.get(f"/api/accas/{ac['id']}", headers=H(a)).json()["locks_at"]
    print("\nPROOF real kickoff in 2 days; week now locks at", locks)
    assert locks.startswith(soon[:16])


def test_unverified_pick_with_forged_odds_freezes_week(c, monkeypatch):
    a = user(c, "a@x.com", "alice")
    g = group(c, a)
    ac = acca(c, a, g["id"])
    fake = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    r = c.post("/api/bets", json={"acca_id": ac["id"], "description": "Arsenal to win", "odds": "10000", "event_id": "made-up",
                                  "pick_type": "home", "home_team": "Arsenal", "away_team": "Chelsea", "commence_time": fake}, headers=H(a))
    print("\nPROOF pick with no sport_key ->", r.status_code, "odds stored:", r.json().get("odds"))
    assert r.status_code == 201 and r.json()["odds"] == "10000"
    db = SessionLocal(); db.query(models.Acca).filter_by(id=ac["id"]).update({"status": "locked"}); db.commit()
    later = datetime.now(timezone.utc) + timedelta(days=60)

    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return later
    monkeypatch.setattr(settlement, "datetime", Later)
    settlement.settle_locked_accas(db)
    a_ = db.query(models.Acca).get(ac["id"]); b_ = db.query(models.Bet).filter_by(acca_id=ac["id"]).one()
    print("PROOF 60 days later: acca", a_.status, "bet result", b_.result); db.close()
    assert a_.status == "locked" and b_.result is None


# ---------------- Outside calls / event loop ----------------

def test_push_has_no_timeout(monkeypatch):
    import requests
    from app import push
    seen = {}

    def fake_post(url, **kw):
        seen["url"], seen["timeout"] = url, kw.get("timeout")
        raise requests.ConnectionError("stop")
    monkeypatch.setattr(requests, "post", fake_post)
    priv, pub = _vapid_keys()
    monkeypatch.setattr(push, "VAPID_PRIVATE_KEY", priv)
    db = SessionLocal()
    u = models.User(email="p@x.com", username="pu", hashed_password="x"); db.add(u); db.commit()
    import json
    db.add(models.PushSubscription(user_id=u.id, endpoint_hash="h", subscription_json=json.dumps({
        "endpoint": "https://10.0.0.5/anything", "keys": {"p256dh": pub, "auth": "8eDyX_uCN0XRhSbY5hs7Hg"}})))
    db.commit()
    push.send_push(db, u.id, {"title": "t"}); db.close()
    print("\nPROOF push POST to", seen.get("url"), "with timeout =", seen.get("timeout"))
    assert seen["timeout"] is None and seen["url"].startswith("https://10.")


def test_push_endpoint_any_host_accepted(c):
    a = user(c, "a@x.com", "alice")
    r = c.post("/api/notifications/subscribe", json={"subscription": {"endpoint": "https://postgres.railway.internal:5432/x",
               "keys": {"p256dh": "k", "auth": "a"}}}, headers=H(a))
    print("\nPROOF internal-host push endpoint ->", r.status_code)
    assert r.status_code == 201


def test_settlement_blocks_event_loop(c, monkeypatch):
    a = user(c, "a@x.com", "alice"); g = group(c, a); ac = acca(c, a, g["id"])
    db = SessionLocal()
    db.add(models.Bet(acca_id=ac["id"], user_id=1, description="d", odds="2", event_id="e", pick_type="home",
                      sport_key="soccer_epl", home_team="Arsenal", away_team="Chelsea",
                      commence_time=datetime.now(timezone.utc) - timedelta(hours=3)))
    db.query(models.Acca).filter_by(id=ac["id"]).update({"status": "locked"}); db.commit(); db.close()
    monkeypatch.setattr(settlement, "get_scores", lambda *a, **k: (time.sleep(2), [])[1])  # a slow odds API answer

    async def run():
        gaps, last = [], time.perf_counter()

        async def ticker():
            nonlocal last
            for _ in range(30):
                await asyncio.sleep(0.1)
                now = time.perf_counter(); gaps.append(now - last); last = now

        async def settle_like_main():  # exactly what auto_settle_bets does each round
            await asyncio.sleep(0.2)
            d = SessionLocal()
            settlement.settle_locked_accas(d)
            d.close()
        await asyncio.gather(ticker(), settle_like_main())
        return max(gaps)
    worst = asyncio.run(run())
    print(f"\nPROOF longest stall of every other request while settlement waited on the odds API: {worst:.2f}s")
    assert worst > 1.5


# ---------------- Browser / rate limits ----------------

def test_push_to_silent_server_never_returns():
    from pywebpush import webpush
    priv, pub = _vapid_keys()
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(5)
    threading.Thread(target=lambda: [srv.accept() for _ in range(5)], daemon=True).start()  # accept, never answer
    sub = {"endpoint": f"https://127.0.0.1:{srv.getsockname()[1]}/push", "keys": {"p256dh": pub, "auth": "8eDyX_uCN0XRhSbY5hs7Hg"}}
    done = threading.Event()

    def go():
        try:  # the same call push.send_push makes
            webpush(subscription_info=sub, data="{}", vapid_private_key=priv, vapid_claims={"sub": "mailto:x@example.com"}, ttl=60)
        except Exception:
            pass
        done.set()
    threading.Thread(target=go, daemon=True).start()
    finished = done.wait(15)
    print("\nPROOF push to a silent server finished within 15s:", finished)
    assert not finished


def test_csp_allows_inline_scripts(c):
    csp = c.get("/api/health").headers["content-security-policy"]
    print("\nPROOF CSP:", csp)
    assert "script-src 'self' 'unsafe-inline'" in csp


def test_endpoints_without_rate_limit():
    from app.routers import auth, groups, groupstats, accas, bets, odds, affiliate, notifications, nudges, devices
    limited = set(limiter._route_limits.keys())
    rows = []
    for m in (auth, groups, groupstats, accas, bets, odds, affiliate, notifications, nudges, devices):
        for r in m.router.routes:
            if f"{r.endpoint.__module__}.{r.endpoint.__name__}" not in limited:
                rows.append(f"{sorted(r.methods)[0]} /api{r.path}")
    print("\nPROOF endpoints with no rate limit:", rows)
    assert rows
