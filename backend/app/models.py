from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# User model - defines the structure of the users table
class User(Base):
    __tablename__ = "users"  # Table name in the database
    
    # Columns
    id = Column(Integer, primary_key=True, index=True)  # Auto-incrementing ID
    email = Column(String, unique=True, index=True, nullable=False)  # Must be unique
    username = Column(String, unique=True, index=True, nullable=False)  # Must be unique
    hashed_password = Column(String, nullable=False)  # We never store plain passwords!
    is_active = Column(Boolean, default=True)  # Can disable accounts if needed
    email_verified = Column(Boolean, default=False)  # Email verification status
    verification_code = Column(String, nullable=True)  # 6-digit verification code
    verification_code_expires = Column(DateTime(timezone=True), nullable=True)  # Code expiry
    verification_attempts = Column(Integer, default=0)  # Failed verification code attempts
    failed_login_attempts = Column(Integer, default=0)  # Failed login attempts
    locked_until = Column(DateTime(timezone=True), nullable=True)  # Account lockout timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Auto timestamp

    # Relationships
    bets = relationship("Bet", back_populates="user")
    memberships = relationship("GroupMember", back_populates="user")

    # When you print a User object, it shows this
    def __repr__(self):
        return f"<User {self.username}>"
    
# Group model - defines the structure of the groups table
class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)  # Optional
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # User ID of creator
    invite_code = Column(String, unique=True, nullable=False) #Invite code
    # Monotonic high-water mark for acca round numbers. Never decremented, so a
    # deleted week leaves an honest gap instead of its number being reissued.
    next_round_number = Column(Integer, nullable=False, default=1, server_default="1")
    # Accas whose first_match_date falls before this drop out of the table, the
    # acca-stats bar and member profiles. Null means count everything ever.
    season_start_date = Column(Date, nullable=True)
    # Anchor Saturday of a week the admin deleted while it was still open and
    # auto-created — the auto-week task must not recreate that weekend. Only
    # the latest skip is kept; a past date is inert.
    skipped_saturday = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    members = relationship("GroupMember", back_populates="group")
    accas = relationship("Acca", back_populates="group")

    def __repr__(self):
        return f"<Group {self.name}>"
    
# Acca model - represents an accumulator for a group
class Acca(Base):
    __tablename__ = "accas"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)  # Which group this acca belongs to
    name = Column(String, nullable=False)  # e.g., "Saturday 1st Feb Acca"
    # Display identity ("Week 3") and stable URL key. Allocated from
    # Group.next_round_number, so it is never reused after a delete.
    round_number = Column(Integer, nullable=True, index=True)
    # min(match_dates). Chronological sort key — created_at is NOT chronological,
    # since a later-dated acca can be created first.
    first_match_date = Column(Date, nullable=True, index=True)
    status = Column(String, default="open")  # open, locked, settled
    match_dates = Column(JSON, nullable=True)  # Array of date strings
    leagues = Column(JSON, nullable=True)  # Array of sport keys
    bet_type = Column(String, default="h2h")  # "h2h" for now
    locks_at = Column(DateTime(timezone=True), nullable=True)  # Locks time for this acca
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # User ID of creator
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    group = relationship("Group", back_populates="accas")
    bets = relationship("Bet", back_populates="acca")

    def __repr__(self):
        return f"<Acca {self.name}>"

# Bet model - represents one person's bet in an acca
class Bet(Base):
    __tablename__ = "bets"

    __table_args__ = (
        UniqueConstraint('acca_id', 'user_id', name='uq_bet_acca_user'),
        UniqueConstraint('acca_id', 'description', name='uq_bet_acca_description'),
    )

    id = Column(Integer, primary_key=True, index=True)
    acca_id = Column(Integer, ForeignKey("accas.id"), nullable=False, index=True)  # Which acca this bet belongs to
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Who created this bet
    description = Column(String, nullable=False)  # e.g., "Man United to win"
    odds = Column(String, nullable=False)  # e.g., "2.5" or "5/2"
    result = Column(String, nullable=True)  # won, lost, void (null = pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Settlement fields
    event_id = Column(String, nullable=True)  # The-Odds-API match ID
    home_team = Column(String, nullable=True)
    away_team = Column(String, nullable=True)
    pick_type = Column(String, nullable=True)  # "home", "away", or "draw"
    sport_key = Column(String, nullable=True)  # e.g., "soccer_epl"
    commence_time = Column(DateTime(timezone=True), nullable=True)  # Match kickoff time

    # Relationships
    user = relationship("User", back_populates="bets")
    acca = relationship("Acca", back_populates="bets")

    def __repr__(self):
        return f"<Bet {self.description}>"
    
# GroupMember model - links users to groups
class GroupMember(Base):
    __tablename__ = "group_members"

    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uq_groupmember_group_user'),
    )

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, default="member")  # member or admin
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    # One IoT display token per membership (sha256 hex of an `apk_...` token).
    # Living on this row means the token dies with the membership — leaving,
    # removal or account deletion revokes it with no extra bookkeeping.
    device_token_hash = Column(String(64), unique=True, nullable=True, index=True)
    device_last_seen_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="memberships")
    group = relationship("Group", back_populates="members")

    def __repr__(self):
        return f"<GroupMember user:{self.user_id} group:{self.group_id}>"

# BookmakerLink model - stores affiliate links for bookmakers
class BookmakerLink(Base):
    __tablename__ = "bookmaker_links"

    id = Column(Integer, primary_key=True, index=True)
    bookmaker_key = Column(String, unique=True, index=True, nullable=False)  # e.g., "bet365"
    display_name = Column(String, nullable=True)  # e.g., "Bet365" or "Betfair Exchange"
    url = Column(String, nullable=False)  # Affiliate link
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<BookmakerLink {self.bookmaker_key}>"

# BookmakerClick model - analytics for tracking bookmaker clicks
class BookmakerClick(Base):
    __tablename__ = "bookmaker_clicks"

    id = Column(Integer, primary_key=True, index=True)
    bookmaker_key = Column(String, index=True, nullable=False)
    acca_id = Column(Integer, nullable=True)  # No FK - analytics data
    user_id = Column(Integer, nullable=True)  # Track which user clicked
    source = Column(String, nullable=True)  # "comparison" or "betslip"
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<BookmakerClick {self.bookmaker_key}>"

# BlacklistedToken model - stores revoked JWT tokens
class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<BlacklistedToken {self.jti}>"

# PushSubscription model - stores web push notification subscriptions
class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    __table_args__ = (
        UniqueConstraint('user_id', 'endpoint_hash', name='uq_push_sub_user_endpoint'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint_hash = Column(String, nullable=False)  # SHA-256 of endpoint URL
    subscription_json = Column(String, nullable=False)  # Full subscription object as JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<PushSubscription user:{self.user_id}>"


class Nudge(Base):
    """One member reminding another to pick. The unique constraint is the
    anti-spam rule: one nudge per target per acca, ever, whoever sends it."""
    __tablename__ = "nudges"

    __table_args__ = (
        UniqueConstraint('acca_id', 'target_user_id', name='uq_nudge_acca_target'),
    )

    id = Column(Integer, primary_key=True, index=True)
    acca_id = Column(Integer, ForeignKey("accas.id", ondelete="CASCADE"), nullable=False, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    nudged_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PickNotification(Base):
    """Marks that we've already sent the 'X made a pick' push for this
    (acca, user). The unique constraint enforces one notification per picker
    per acca, ever — so a re-pick (delete + re-create) never re-notifies.
    The row deliberately survives bet deletion, which is why first-pick can't
    be inferred from the bets table."""
    __tablename__ = "pick_notifications"

    __table_args__ = (
        UniqueConstraint('acca_id', 'user_id', name='uq_pick_notif_acca_user'),
    )

    id = Column(Integer, primary_key=True, index=True)
    acca_id = Column(Integer, ForeignKey("accas.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
