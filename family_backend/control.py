"""Persistent admission, budgets and job metadata shared by all app adapters.

Amounts are USD micro-units. Compute charges are conservative estimates, not
provider invoices. No provider credential or input payload is stored here.
"""
import contextvars
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import functools
import hashlib
import inspect
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo


class ControlError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def micros(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0:
            raise ValueError()
        return int((amount * 1_000_000).to_integral_value(rounding=ROUND_CEILING))
    except (InvalidOperation, ValueError, TypeError, OverflowError):
        raise ControlError("invalid_cost", "Cost must be a finite, non-negative USD amount.") from None


ENDPOINT_CAPABILITIES = {
    "52cjk52hgbwag1": "fast", "c3lm36gdhpctl2": "reasoning", "936leprwfzb9gr": "vision",
    "black-forest-labs-flux-1-schnell": "image", "black-forest-labs-flux-1-dev": "image_quality",
    "wan-2-2-i2v-720": "video", "b8yk3ju5yc5kqx": "voice",
}
HOURLY_USD = {"fast": "0.75", "reasoning": "1.75", "vision": "1.75", "voice": "0.75"}
IDLE_SECONDS = {"fast": 60, "reasoning": 600, "vision": 600, "voice": 300}
TERMINAL_STATES = {"completed", "failed", "cancelled", "rejected", "resolved"}
ACTIVE_STATES = {"reserved", "submitting", "queued", "running", "unknown", "cancel_requested"}


@dataclass
class Limits:
    daily_usd: str = "2.00"
    monthly_usd: str = "20.00"
    timezone: str = "Europe/Helsinki"
    max_concurrent: int = 2
    max_video_seconds: int = 5
    max_videos_per_turn: int = 1
    warning_fraction: float = 0.8
    daily_counts: dict = field(default_factory=lambda: {
        "fast": 100, "reasoning": 20, "vision": 20, "image": 10,
        "image_quality": 3, "video": 2, "voice": 10,
    })
    monthly_counts: dict = field(default_factory=lambda: {"video": 10, "reasoning": 100})

    def validate(self):
        if micros(self.daily_usd) <= 0 or micros(self.monthly_usd) <= 0:
            raise ControlError("invalid_policy", "Daily and monthly budgets must be positive.")
        try:
            ZoneInfo(self.timezone)
        except Exception:
            raise ControlError("invalid_policy", "Unknown budget timezone.") from None
        if (type(self.max_concurrent) is not int or type(self.max_video_seconds) is not int
                or not 1 <= self.max_concurrent <= 8 or not 1 <= self.max_video_seconds <= 5):
            raise ControlError("invalid_policy", "Concurrency must be 1–8 and video duration 1–5 seconds.")
        if (type(self.max_videos_per_turn) is not int or not isinstance(self.warning_fraction, (int, float))
                or not 1 <= self.max_videos_per_turn <= 3 or not 0.5 <= self.warning_fraction < 1):
            raise ControlError("invalid_policy", "Invalid video count or warning threshold.")
        for group in (self.daily_counts, self.monthly_counts):
            if not isinstance(group, dict):
                raise ControlError("invalid_policy", "Capability limits must be objects.")
            if any(k not in set(ENDPOINT_CAPABILITIES.values()) or type(v) is not int or v < 0 for k, v in group.items()):
                raise ControlError("invalid_policy", "Capability counts must be non-negative integers.")
        return self


@dataclass(frozen=True)
class OperationContext:
    owner: str
    conversation: str
    turn: str


CURRENT_CONTEXT = contextvars.ContextVar("family_operation", default=None)
CURRENT_JOB = contextvars.ContextVar("family_job", default=None)


def context_for(user=None, metadata=None, chat_id=None, message_id=None):
    existing = CURRENT_CONTEXT.get()
    user = user or {}
    owner = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    if not owner:
        if existing:
            return existing
        raise ControlError("authentication_required", "An authenticated Family AI user is required.")
    metadata = metadata or {}
    conversation = chat_id or metadata.get("chat_id") or "unsaved"
    turn = message_id or metadata.get("message_id") or metadata.get("idempotency_key")
    if not turn:
        raise ControlError("missing_turn", "A stable message ID or idempotency key is required before starting GPU work.")
    for value in (owner, conversation, turn):
        if not isinstance(value, str) or not value or len(value) > 256:
            raise ControlError("invalid_context", "Invalid operation identity.")
    return OperationContext(owner, conversation, turn)


@contextmanager
def operation_context(context):
    token = CURRENT_CONTEXT.set(context)
    try:
        yield
    finally:
        CURRENT_CONTEXT.reset(token)


def controlled_tool(function):
    signature = inspect.signature(function)

    @functools.wraps(function)
    async def wrapper(*args, **kwargs):
        values = signature.bind(*args, **kwargs).arguments
        context = context_for(values.get("__user__"), chat_id=values.get("__chat_id__"),
                              message_id=values.get("__message_id__"))
        job_token = CURRENT_JOB.set(None)
        try:
            with operation_context(context):
                return await function(*args, **kwargs)
        finally:
            CURRENT_JOB.reset(job_token)
    return wrapper


def default_ledger():
    # Production defaults live under the existing persistent app data mount.
    directory = Path(os.environ.get("DATA_DIR", "/app/backend/data")) / "family-ai"
    path = Path(os.environ.get("FAMILY_CONTROL_DB", str(directory / "control.sqlite3")))
    return Ledger(path)


class Ledger:
    def __init__(self, path, clock=time.time):
        self.path = Path(path)
        self.clock = clock
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.path.is_symlink():
            raise ControlError("unsafe_path", "Control database must not be a symlink.")
        with self.connection() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, owner TEXT NOT NULL, conversation TEXT NOT NULL, turn TEXT NOT NULL,
              capability TEXT NOT NULL, endpoint TEXT NOT NULL, digest TEXT NOT NULL, request_key TEXT NOT NULL,
              state TEXT NOT NULL, reserved INTEGER NOT NULL, charged INTEGER NOT NULL DEFAULT 0,
              created REAL NOT NULL, updated REAL NOT NULL, day TEXT NOT NULL, month TEXT NOT NULL,
              provider_id TEXT, cancel_requested INTEGER NOT NULL DEFAULT 0, output TEXT,
              UNIQUE(owner, request_key));
            CREATE INDEX IF NOT EXISTS jobs_budget ON jobs(month, day, state);
            CREATE INDEX IF NOT EXISTS jobs_owner ON jobs(owner, conversation, created);
            CREATE TABLE IF NOT EXISTS events (
              sequence INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, kind TEXT NOT NULL,
              data TEXT NOT NULL, created REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS events_job ON events(job_id, sequence);
            CREATE TABLE IF NOT EXISTS assets (
              id TEXT PRIMARY KEY, owner TEXT NOT NULL, job_id TEXT NOT NULL, info TEXT NOT NULL,
              provider_url TEXT, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS classifications (
              key TEXT PRIMARY KEY, route TEXT NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS billing (
              id TEXT PRIMARY KEY, period TEXT NOT NULL, amount INTEGER NOT NULL, observed REAL NOT NULL,
              source TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS voice_sessions (
              owner TEXT PRIMARY KEY, conversation TEXT NOT NULL, state TEXT NOT NULL, expires REAL NOT NULL);
            """)
            db.execute("INSERT OR IGNORE INTO policy VALUES(1,?)", (json.dumps(asdict(Limits())),))
        os.chmod(self.path, 0o600)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=5000")
        try:
            yield db
        finally:
            if db.in_transaction:
                db.rollback()
            db.close()

    def policy(self, db=None):
        if db is None:
            with self.connection() as connection:
                return self.policy(connection)
        return Limits(**json.loads(db.execute("SELECT value FROM policy WHERE id=1").fetchone()[0])).validate()

    def set_policy(self, value):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = asdict(self.policy(db))
            if not isinstance(value, dict):
                raise ControlError("invalid_policy", "Policy must be an object.")
            updates = dict(value)
            for key in ("daily_counts", "monthly_counts"):
                if isinstance(updates.get(key), dict):
                    updates[key] = {**previous[key], **updates[key]}
            try:
                policy = Limits(**{**previous, **updates}).validate()
            except TypeError:
                raise ControlError("invalid_policy", "Unknown or missing policy fields.") from None
            db.execute("UPDATE policy SET value=? WHERE id=1", (json.dumps(asdict(policy)),))
            db.commit()
        return asdict(policy)

    def periods(self, policy=None):
        now = datetime.fromtimestamp(self.clock(), ZoneInfo((policy or self.policy()).timezone))
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")

    @staticmethod
    def capability(endpoint):
        try:
            return ENDPOINT_CAPABILITIES[endpoint]
        except KeyError:
            raise ControlError("unpriced_endpoint", "Endpoint is not in the approved capability/rate catalog.") from None

    @staticmethod
    def estimate(capability, timeout=600, duration=5):
        if capability == "image":
            return micros("0.003")
        if capability == "image_quality":
            return micros("0.024")  # Conservative ceiling; provider-reported cost remains distinct.
        if capability == "video":
            if type(duration) is not int or duration != 5:
                raise ControlError("video_duration", "The current Wan profile supports a five-second clip; a lower duration cap disables this profile.")
            return micros("0.30")
        return micros(Decimal(HOURLY_USD[capability]) * Decimal(timeout + IDLE_SECONDS[capability]) / 3600)

    def _event(self, db, job_id, kind, data):
        encoded = json.dumps(data, ensure_ascii=False)
        if len(encoded.encode()) > 131072:
            raise ControlError("event_too_large", "A job event exceeded the storage limit.")
        db.execute("INSERT INTO events(job_id,kind,data,created) VALUES(?,?,?,?)", (job_id, kind, encoded, self.clock()))

    def reserve(self, context, endpoint, payload, timeout=600, duration=5):
        capability = self.capability(endpoint)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        request_key = hashlib.sha256(f"{context.conversation}:{context.turn}:{capability}:{digest}".encode()).hexdigest()
        now = self.clock()
        estimate = self.estimate(capability, timeout, duration)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            policy = self.policy(db)
            day, month = self.periods(policy)
            old = db.execute("SELECT * FROM jobs WHERE owner=? AND request_key=?", (context.owner, request_key)).fetchone()
            # Catch duplicate submissions after a lost response even when the
            # frontend assigned a new assistant message ID. Never auto-resubmit.
            if old is None:
                old = db.execute("SELECT * FROM jobs WHERE owner=? AND conversation=? AND endpoint=? AND digest=? AND (created>? OR state IN ('reserved','submitting','queued','running','unknown','cancel_requested')) ORDER BY created DESC LIMIT 1",
                                 (context.owner, context.conversation, endpoint, digest, now - 120)).fetchone()
            if old:
                db.commit()
                return self.get(context.owner, old["id"]), False
            if capability == "video":
                if not 1 <= duration <= policy.max_video_seconds:
                    raise ControlError("video_duration", "Video exceeds the configured duration limit.")
                count = db.execute("SELECT count(*) FROM jobs WHERE owner=? AND conversation=? AND turn=? AND capability='video' AND state!='rejected'",
                                   (context.owner, context.conversation, context.turn)).fetchone()[0]
                if count >= policy.max_videos_per_turn:
                    raise ControlError("video_count", "Video generation count for this turn has been reached.")
            if capability == "reasoning":
                count = db.execute("SELECT count(*) FROM jobs WHERE owner=? AND conversation=? AND turn=? AND capability='reasoning' AND state!='rejected'",
                                   (context.owner, context.conversation, context.turn)).fetchone()[0]
                if count:
                    raise ControlError("reasoning_loop", "This turn already used the reasoning specialist; reuse its result.")
            active = db.execute("SELECT count(*) FROM jobs WHERE state IN ('reserved','submitting','queued','running','unknown','cancel_requested')").fetchone()[0]
            if active >= policy.max_concurrent:
                raise ControlError("concurrency_limit", "Family AI has reached its concurrent-operation limit.")
            for column, period, ceiling, counts in [
                ("day", day, micros(policy.daily_usd), policy.daily_counts),
                ("month", month, micros(policy.monthly_usd), policy.monthly_counts),
            ]:
                spent = db.execute(f"SELECT COALESCE(sum(charged+reserved),0) FROM jobs WHERE {column}=?", (period,)).fetchone()[0]
                if spent + estimate > ceiling:
                    raise ControlError("budget_exceeded", f"The {column} budget cannot reserve this operation's estimated cost.")
                count = db.execute(f"SELECT count(*) FROM jobs WHERE {column}=? AND capability=? AND state!='rejected'", (period, capability)).fetchone()[0]
                if capability in counts and count >= counts[capability]:
                    raise ControlError("capability_limit", f"The {column} usage limit for {capability} has been reached.")
            job_id = str(uuid.uuid4())
            db.execute("INSERT INTO jobs(id,owner,conversation,turn,capability,endpoint,digest,request_key,state,reserved,created,updated,day,month) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (job_id, context.owner, context.conversation, context.turn, capability, endpoint, digest, request_key, "reserved", estimate, now, now, day, month))
            self._event(db, job_id, "job.created", {"job_id": job_id, "capability": capability, "estimated_usd": estimate / 1_000_000, "cost_kind": "reservation"})
            db.commit()
            return self.get(context.owner, job_id), True

    def get(self, owner, job_id):
        with self.connection() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=? AND owner=?", (job_id, owner)).fetchone()
            if row is None:
                raise ControlError("not_found", "Job not found.")
            result = dict(row)
            result["output"] = json.loads(result["output"]) if result["output"] else None
            return result

    def transition(self, owner, job_id, state, provider_id=None):
        if state not in ACTIVE_STATES | TERMINAL_STATES:
            raise ControlError("invalid_state", "Unknown job state.")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE id=? AND owner=?", (job_id, owner)).fetchone()
            if row is None:
                raise ControlError("not_found", "Job not found.")
            if row["state"] in TERMINAL_STATES:
                db.commit()
                return
            if state in TERMINAL_STATES:
                raise ControlError("invalid_state", "Use finish to settle terminal jobs.")
            db.execute("UPDATE jobs SET state=?,provider_id=COALESCE(?,provider_id),updated=? WHERE id=?", (state, provider_id, self.clock(), job_id))
            if state != row["state"]:
                self._event(db, job_id, "job.state", {"state": state, "provider_job_id": provider_id or row["provider_id"]})
            db.commit()

    def finish(self, owner, job_id, state, output=None, charge=None):
        if state not in TERMINAL_STATES:
            raise ControlError("invalid_state", "Unknown terminal job state.")
        encoded = json.dumps(output, ensure_ascii=False) if output is not None else None
        if encoded and len(encoded.encode()) > 2_000_000:
            raise ControlError("result_too_large", "Job output exceeded the persistence limit.")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE id=? AND owner=?", (job_id, owner)).fetchone()
            if row is None:
                raise ControlError("not_found", "Job not found.")
            if row["state"] in TERMINAL_STATES:
                db.commit()
                return
            # Without a provider invoice keep the conservative reservation as
            # an estimated charge; do not pretend token usage equals GPU billing.
            settled = row["reserved"] if charge is None else micros(charge)
            db.execute("UPDATE jobs SET state=?,charged=?,reserved=0,output=?,updated=? WHERE id=?",
                       (state, settled, encoded, self.clock(), job_id))
            self._event(db, job_id, "job.finished", {"state": state, "estimated_charge_usd": settled / 1_000_000})
            db.commit()

    def event(self, owner, job_id, kind, data):
        self.get(owner, job_id)
        with self.connection() as db:
            self._event(db, job_id, kind, data)

    def events(self, owner, job_id, after=0):
        self.get(owner, job_id)
        with self.connection() as db:
            return [{"id": r["sequence"], "type": r["kind"], "data": json.loads(r["data"]), "created": r["created"]}
                    for r in db.execute("SELECT * FROM events WHERE job_id=? AND sequence>? ORDER BY sequence LIMIT 512", (job_id, after))]

    def cancel(self, owner, job_id):
        row = self.get(owner, job_id)
        if row["state"] in TERMINAL_STATES:
            return row
        with self.connection() as db:
            db.execute("UPDATE jobs SET cancel_requested=1,updated=? WHERE id=? AND owner=?", (self.clock(), job_id, owner))
        self.event(owner, job_id, "job.cancel_requested", {"best_effort": True})
        return self.get(owner, job_id)

    def usage(self, owner=None):
        policy = self.policy()
        day, month = self.periods(policy)
        result = {"currency": "USD", "scope": "Family AI governed operations only", "timezone": policy.timezone,
                  "cost_kind": "conservative_estimate", "provider_hard_cap": False, "periods": {}}
        with self.connection() as db:
            for column, period, ceiling in [("day", day, micros(policy.daily_usd)), ("month", month, micros(policy.monthly_usd))]:
                rows = db.execute(f"SELECT capability,sum(CASE WHEN state!='rejected' THEN 1 ELSE 0 END) count,sum(charged) charged,sum(reserved) reserved FROM jobs WHERE {column}=? GROUP BY capability", (period,)).fetchall()
                total = sum((r["charged"] or 0) + (r["reserved"] or 0) for r in rows)
                result["periods"][column] = {"period": period, "estimated_and_reserved_usd": total / 1_000_000,
                    "limit_usd": ceiling / 1_000_000, "warning": total >= ceiling * policy.warning_fraction,
                    "capabilities": [{"capability": r["capability"], "count": r["count"],
                        "charged_usd": (r["charged"] or 0) / 1_000_000,
                        "reserved_usd": (r["reserved"] or 0) / 1_000_000} for r in rows]}
            result["provider_billing"] = [{"period": r["period"], "amount_usd": r["amount"] / 1_000_000,
                "observed": r["observed"], "source": r["source"], "provenance": "admin_imported"}
                for r in db.execute("SELECT period,amount,observed,source FROM billing ORDER BY observed DESC LIMIT 12")]
        return result

    def quote(self, endpoint, timeout=600, duration=5):
        capability = self.capability(endpoint)
        policy = self.policy()
        estimate = self.estimate(capability, timeout, duration)
        usage = self.usage()
        if capability == "video" and not 1 <= duration <= policy.max_video_seconds:
            raise ControlError("video_duration", "Video exceeds the configured duration limit.")
        allowed = all(p["estimated_and_reserved_usd"] + estimate / 1_000_000 <= p["limit_usd"] for p in usage["periods"].values())
        for period, counts in [("day", policy.daily_counts), ("month", policy.monthly_counts)]:
            used = next((c["count"] for c in usage["periods"][period]["capabilities"] if c["capability"] == capability), 0)
            if capability in counts and used >= counts[capability]:
                allowed = False
        return {"capability": capability, "estimated_usd": estimate / 1_000_000,
                "currency": "USD", "allowed_at_quote_time": allowed, "cost_kind": "conservative_estimate",
                "reservation_required": True, "includes_gpu_idle_reserve": capability in HOURLY_USD}

    def preflight_video(self, context, endpoint, timeout, duration, needs_image):
        quote = self.quote(endpoint, timeout, duration)
        if not quote["allowed_at_quote_time"]:
            raise ControlError("budget_exceeded", "Video budget or usage limit has been reached.")
        with self.connection() as db:
            count = db.execute("SELECT count(*) FROM jobs WHERE owner=? AND conversation=? AND turn=? AND capability='video' AND state!='rejected'",
                               (context.owner, context.conversation, context.turn)).fetchone()[0]
        if count >= self.policy().max_videos_per_turn:
            raise ControlError("video_count", "Video generation count for this turn has been reached.")
        extra = 0.003 if needs_image else 0
        if any(p["estimated_and_reserved_usd"] + quote["estimated_usd"] + extra > p["limit_usd"] for p in self.usage()["periods"].values()):
            raise ControlError("budget_exceeded", "The starting image and video exceed the remaining budget.")
        return {**quote, "estimated_usd": quote["estimated_usd"] + extra}

    def list_jobs(self, owner, limit=50):
        with self.connection() as db:
            return [self.get(owner, r[0]) for r in db.execute("SELECT id FROM jobs WHERE owner=? ORDER BY created DESC LIMIT ?", (owner, min(max(limit, 1), 100)))]

    def reconciliation_jobs(self):
        # Admin billing recovery needs IDs, not another family member's output.
        with self.connection() as db:
            return [{"id": r["id"], "endpoint": r["endpoint"], "capability": r["capability"],
                "provider_id": r["provider_id"], "state": r["state"], "created": r["created"],
                "reserved_usd": r["reserved"] / 1_000_000} for r in db.execute(
                    "SELECT id,endpoint,capability,provider_id,state,created,reserved FROM jobs WHERE state='unknown' ORDER BY created LIMIT 100")]

    def resolve_unknown(self, job_id, operator, reason, amount=None):
        if not isinstance(reason, str) or not 12 <= len(reason) <= 500:
            raise ControlError("invalid_request", "Reconciliation requires a reason after provider review.")
        with self.connection() as db:
            row = db.execute("SELECT owner FROM jobs WHERE id=? AND state='unknown'", (job_id,)).fetchone()
        if row is None:
            raise ControlError("not_found", "Uncertain job not found.")
        self.finish(row["owner"], job_id, "resolved", {"operator_id": operator, "operator_reason": reason}, amount)
        result = self.get(row["owner"], job_id)
        return {"id": job_id, "state": result["state"], "estimated_charge_usd": result["charged"] / 1_000_000}

    def billing_snapshot(self, period, amount, source="RunPod billing API"):
        if not isinstance(period, str) or len(period) > 32 or source != "RunPod billing API":
            raise ControlError("invalid_billing", "Invalid billing snapshot source or period.")
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO billing VALUES(?,?,?,?,?)", (period, period, micros(amount), self.clock(), source))

    def voice(self, owner, conversation="unsaved", activate=False, stop=False):
        now = self.clock()
        with self.connection() as db:
            if activate:
                db.execute("INSERT OR REPLACE INTO voice_sessions VALUES(?,?,?,?)", (owner, conversation, "starting", now + 300))
            elif stop:
                db.execute("DELETE FROM voice_sessions WHERE owner=?", (owner,))
            row = db.execute("SELECT conversation,state,expires FROM voice_sessions WHERE owner=? AND expires>?", (owner, now)).fetchone()
            return dict(row) if row else {"state": "off", "expires": None, "conversation": None}

    def mark_voice_ready(self, owner):
        with self.connection() as db:
            db.execute("UPDATE voice_sessions SET state='ready' WHERE owner=? AND expires>?", (owner, self.clock()))

    def remember_asset(self, owner, job_id, info, provider_url):
        self.get(owner, job_id)
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO assets VALUES(?,?,?,?,?,?)", (info["id"], owner, job_id, json.dumps(info), provider_url, self.clock()))

    def asset_for_job(self, owner, job_id):
        self.get(owner, job_id)
        with self.connection() as db:
            row = db.execute("SELECT info FROM assets WHERE owner=? AND job_id=? ORDER BY created DESC LIMIT 1", (owner, job_id)).fetchone()
            return json.loads(row[0]) if row else None

    def asset_source(self, owner, asset_id):
        with self.connection() as db:
            row = db.execute("SELECT provider_url FROM assets WHERE id=? AND owner=?", (asset_id, owner)).fetchone()
            if row is None:
                raise ControlError("not_found", "Asset not found.")
            return row[0]

    def is_warm(self, endpoint, window=45):
        with self.connection() as db:
            return bool(db.execute("SELECT 1 FROM jobs WHERE endpoint=? AND state='completed' AND updated>? LIMIT 1",
                                   (endpoint, self.clock() - window)).fetchone())

    def cached_route(self, key, route=None):
        with self.connection() as db:
            if route is not None:
                if route not in {"fast", "pro"}:
                    raise ControlError("invalid_route", "Unknown classification result.")
                db.execute("INSERT OR REPLACE INTO classifications VALUES(?,?,?)", (key, route, self.clock() + 300))
                return route
            row = db.execute("SELECT route FROM classifications WHERE key=? AND expires>?", (key, self.clock())).fetchone()
            return row[0] if row else None


class Operation:
    """One durable provider submission. Replays are never resubmitted."""
    def __init__(self, endpoint, payload, timeout=600, duration=5):
        self.context = CURRENT_CONTEXT.get()
        if self.context is None:
            raise ControlError("authentication_required", "An authenticated operation context is required.")
        self.ledger = default_ledger()
        self.row, self.created = self.ledger.reserve(self.context, endpoint, payload, timeout, duration)
        self.id = self.row["id"]
        self.started = False
        self.finished = False
        if self.created:
            usage = self.ledger.usage()
            warnings = {k: v for k, v in usage["periods"].items() if v["warning"]}
            if warnings:
                self.event("usage.warning", warnings)

    def replay(self):
        if self.created:
            return None
        if self.row["state"] == "completed" and self.row["output"] is not None:
            return self.row["output"]
        raise ControlError("duplicate_operation", f"This operation already exists ({self.id}, {self.row['state']}). Inspect it before retrying.")

    def submitting(self):
        self.ledger.transition(self.context.owner, self.id, "submitting")
        self.started = True

    def accepted(self, provider_id):
        self.ledger.transition(self.context.owner, self.id, "queued", provider_id)

    def progress(self, status):
        # A completion racing with cancel must keep the completed result.
        if status in {"IN_QUEUE", "IN_PROGRESS"} and self.ledger.get(self.context.owner, self.id)["cancel_requested"]:
            raise ControlError("cancel_requested", "Cancellation requested; no replacement job will be submitted.")
        if status in {"IN_QUEUE", "IN_PROGRESS"}:
            self.ledger.transition(self.context.owner, self.id, "queued" if status == "IN_QUEUE" else "running")

    def event(self, kind, data):
        self.ledger.event(self.context.owner, self.id, kind, data)

    def complete(self, output, cost=None):
        self.ledger.finish(self.context.owner, self.id, "completed", output, cost)
        self.finished = True

    def terminal(self, status):
        self.ledger.finish(self.context.owner, self.id, "cancelled" if status == "CANCELLED" else "failed")
        self.finished = True

    def rejected(self):
        self.ledger.finish(self.context.owner, self.id, "rejected", charge=0)
        self.finished = True

    def unresolved(self):
        if self.finished or not self.created:
            return
        if self.started:
            self.ledger.transition(self.context.owner, self.id, "unknown")
        else:
            self.ledger.finish(self.context.owner, self.id, "rejected", charge=0)

    def public(self):
        return {"job_id": self.id, "capability": self.row["capability"],
                "estimated_usd": self.row["reserved"] / 1_000_000, "cost_kind": "reservation"}
