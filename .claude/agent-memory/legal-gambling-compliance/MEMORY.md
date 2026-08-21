# AccaPicks Legal/Compliance Memory

## Document landscape (as of Feb 2026 docs review)
- FOUR legal-doc artifacts exist, and they are NOT kept in sync:
  - `/home/user/accapicks/termsofservice.txt` and `privacypolicy.txt` — root-level **unfilled templates**
    (still have `[DATE]`, `[INSERT ...]`, `[EMAIL]` placeholders). NOT rendered anywhere in the app.
  - `src/components/TermsOfService.jsx` and `PrivacyPolicy.jsx` — the **actual live/rendered** docs, with
    real date (was "February 5, 2026") and real contact email (glen.dev@outlook.com).
  - The .txt files are a stale superset: ToS.txt has 27 sections incl. Waiver, Entire Agreement,
    Assignment, No Agency Relationship, Force Majeure — **all five are missing from the live .jsx**.
    PrivacyPolicy.txt has a CCPA section and a Glossary section that are **missing from the live .jsx**.
  - Always diff .txt vs .jsx section-by-section when asked to review legal docs — don't assume they're
    duplicates. Treat .jsx as ground truth for "what users actually see"; flag drift as its own finding.

## Positioning anchor
- The "not gambling / no real money" claim is genuinely well-supported in the live docs: ToS §3 (Nature
  of Service), §9 (Responsible Gambling with BeGambleAware/GamCare links), Privacy §2.2. Affiliate/
  bookmaker-comparison feature was already anticipated and covered (ToS §6/§7, Privacy §6.2) — don't
  flag affiliate links as a doc gap; the real exposure there is UI-level disclosure (label near the
  link itself), which UK ASA/CAP Code and CMA guidance require regardless of what the ToS says.

## Known gaps found in Aug 2026 review (push/nudge/invite-preview batch)
- Push notifications (backend/app/routers/bets.py ~line 243: `f"{username} picked {description} in your
  group acca"` sent to every other group member via `push.py: send_push`) and the nudge feature
  (`routers/nudges.py`) are **not mentioned anywhere** in either Privacy Policy version — no push
  notification section, no mention of interpersonal data flows via push, no push service listed as a
  data recipient in §6 (Data Sharing). This is a real gap, not paranoia — it's a new recipient category
  (browser push infra) and a new purpose (username+activity broadcast to other individuals' devices).
- Public invite-preview (`GET` handled by `preview_invite` in `backend/app/routers/groups.py` ~line 103,
  returns `{name, member_count}` with **no auth check**) exposes group name + member count to anyone with
  the link, pre-signup. Real risk only if group names contain real names (common in informal friend-group
  naming) — flagged as SHOULD-leaning-MUST rather than a flat MUST since it's data-dependent.
- Illustrative notional stake figure (£10 vs £5) appears in NEITHER legal doc (grepped both — no
  currency-figure text besides the unrelated £100 liability cap) — always a non-issue for legal docs
  when it changes, since it's UI-only and doesn't touch the no-real-money positioning either way.

## Process note
- For this project, cross-check prompt's factual claims against actual code (grep the relevant router)
  before writing the legal assessment — it's fast and the actual notification string / endpoint response
  shape matters for precise section-citing. Did this via Grep/Read on bets.py and groups.py.
