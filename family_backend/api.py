"""Authenticated control API mounted into Open WebUI; no frontend replacement.

Core dispatch is framework-independent so the same handlers can be exercised
over real local HTTP in tests. Production authentication stays in Open WebUI.
"""
import asyncio
import json
import re
import time
from dataclasses import asdict
from urllib.parse import urlsplit

from family_backend.control import ControlError, Ledger, default_ledger, OperationContext, ENDPOINT_CAPABILITIES, configured_runpod_key
from family_backend.speech import install_speech_api
from family_backend.account import RunPodAccount


def check_origin(headers, unsafe):
    if not unsafe:
        return
    origin = headers.get("origin")
    host = headers.get("host", "")
    if origin and (urlsplit(origin).scheme not in {"https", "http"} or urlsplit(origin).netloc != host):
        raise ControlError("origin_forbidden", "Cross-origin writes are not allowed.")
    if not headers.get("authorization", "").startswith("Bearer ") and not origin:
        raise ControlError("origin_required", "Cookie-authenticated writes require a same-origin Origin header.")


def public_job(row):
    return {key: row[key] for key in (
        "id", "conversation", "turn", "capability", "endpoint", "state", "created", "updated",
        "provider_id", "cancel_requested", "output",
    )} | {"reserved_usd": row["reserved"] / 1_000_000, "estimated_charge_usd": row["charged"] / 1_000_000,
          "provider_reported_usd": row["provider_reported"] / 1_000_000 if row["provider_reported"] is not None else None,
          "cost_basis": "provider_reported" if row["provider_reported"] is not None else
                        "not_submitted" if row["state"] == "rejected" else
                        "admin_estimate" if row["state"] == "resolved" else
                        "reservation" if row["reserved"] else "unreconciled_estimate"}


class ControlAPI:
    def __init__(self, ledger=None, provider_call=None, account=None):
        self.ledger = ledger or default_ledger()
        self.provider_call = provider_call
        self.health_cache = None
        self.account = account or RunPodAccount()

    async def dispatch(self, method, path, user, body=None, headers=None):
        if (not isinstance(user, dict) or not isinstance(user.get("id"), str)
                or not user.get("id") or user.get("role") not in {"user", "admin"}):
            raise ControlError("authentication_required", "An authenticated, verified user is required.")
        headers = {k.lower(): v for k, v in (headers or {}).items()}
        check_origin(headers, method not in {"GET", "HEAD"})
        body = body or {}
        owner = user["id"]
        if method == "GET" and path == "/account":
            if user["role"] != "admin":
                raise ControlError("forbidden", "Only the administrator can view the RunPod account balance.")
            return await self.account.get()
        if method == "GET" and path == "/usage":
            usage = self.ledger.usage()
            if user["role"] != "admin":
                usage.pop("provider_billing", None)
            return usage
        if method == "GET" and path == "/jobs":
            return {"jobs": [public_job(j) for j in self.ledger.list_jobs(owner)]}
        if method == "GET" and path == "/capabilities":
            return {"version": "1", "capabilities": ["fast", "reasoning", "vision", "image", "image_quality", "video", "voice"],
                    "voice_activation": "manual", "guarded_voice_prefix": "/api/v1/family/voice", "public_default_changed": False,
                    "chat_transport": "/api/chat/completions", "provider_hard_spending_cap": False}
        if method == "GET" and path == "/models/state":
            if self.provider_call is None:
                raise ControlError("provider_unavailable", "Provider status access is not configured.")
            if self.health_cache and self.health_cache[0] > time.time() - 5:
                return self.health_cache[1]
            values = []
            for endpoint in ["52cjk52hgbwag1", "c3lm36gdhpctl2", "936leprwfzb9gr", "b8yk3ju5yc5kqx"]:
                try:
                    health = await self.provider_call("GET", endpoint, "health")
                    workers = health.get("workers", {})
                    state = ("running" if workers.get("running", 0) else "starting" if workers.get("initializing", 0)
                             else "standby" if workers.get("ready", 0) or workers.get("idle", 0)
                             else "throttled" if workers.get("throttled", 0)
                             else "unhealthy" if workers.get("unhealthy", 0) else "idle")
                    values.append({"endpoint": endpoint, "capability": ENDPOINT_CAPABILITIES[endpoint],
                                   "state": state, "worker_counts": workers,
                                   "note": "Standby/health rollups do not prove a loaded or billable GPU."})
                except ControlError:
                    values.append({"endpoint": endpoint, "state": "unavailable"})
            result = {"observed_at": time.time(), "models": values, "wakes_voice": False}
            self.health_cache = (time.time(), result)
            return result
        if path == "/policy":
            if user["role"] != "admin":
                raise ControlError("forbidden", "Only the admin can inspect or change budget policy.")
            if method == "GET":
                return asdict(self.ledger.policy())
            if method == "POST":
                return self.ledger.set_policy(body)
        if method == "POST" and path == "/quote":
            endpoint = body.get("endpoint")
            timeout, duration = body.get("timeout_seconds", 600), body.get("duration_seconds", 5)
            if type(timeout) is not int or not 1 <= timeout <= 1800 or type(duration) is not int:
                raise ControlError("invalid_request", "Invalid quote timeout or duration.")
            return self.ledger.quote(endpoint, timeout, duration)
        if path == "/voice/session":
            if method == "GET":
                return {**self.ledger.voice(owner), "manual": True, "minimum_workers": 0}
            if method == "DELETE":
                return self.ledger.voice(owner, stop=True)
            # Starting is deliberately handled by the manual Action, which
            # performs the bounded, budgeted provider probe with the stored key.
        if method == "POST" and path == "/billing":
            if user["role"] != "admin":
                raise ControlError("forbidden", "Only the admin can import provider billing snapshots.")
            self.ledger.billing_snapshot(body.get("period"), body.get("amount_usd"))
            return {"imported": True, "provenance": "admin-imported RunPod billing snapshot", "hard_cap": False}
        if method == "GET" and path == "/reconciliation":
            if user["role"] != "admin":
                raise ControlError("forbidden", "Only the admin can review uncertain billing operations.")
            return {"jobs": self.ledger.reconciliation_jobs()}
        match = re.fullmatch(r"/jobs/([a-f0-9-]{36})(/cancel|/retry|/resolve|/refresh)?", path)
        if match:
            job_id, operation = match.groups()
            if method == "POST" and operation == "/resolve":
                if user["role"] != "admin":
                    raise ControlError("forbidden", "Only the admin can reconcile an uncertain operation.")
                return self.ledger.resolve_unknown(job_id, owner, body.get("reason"), body.get("estimated_charge_usd"))
            row = self.ledger.get(owner, job_id)
            if method == "GET" and operation is None:
                return public_job(row)
            if method == "POST" and operation == "/cancel":
                updated = self.ledger.cancel(owner, job_id)
                if self.provider_call and row["provider_id"] and row["state"] not in {"completed", "failed", "cancelled", "resolved", "rejected"}:
                    try:
                        result = await self.provider_call("POST", row["endpoint"], "cancel/" + row["provider_id"])
                        if result.get("status") == "CANCELLED":
                            self.ledger.finish(owner, job_id, "cancelled")
                    except ControlError:
                        pass  # Cancellation remains requested, not falsely confirmed.
                return public_job(self.ledger.get(owner, job_id))
            if method == "POST" and operation == "/refresh":
                if not self.provider_call or not row["provider_id"]:
                    raise ControlError("unresolved_submission", "No known provider job can be refreshed; review RunPod Requests first.")
                result = await self.provider_call("GET", row["endpoint"], "status/" + row["provider_id"])
                status = result.get("status")
                if status == "COMPLETED":
                    self.ledger.finish(owner, job_id, "completed", {"recovered_provider_output": result.get("output"), "automatic_tool_execution": False})
                elif status in {"FAILED", "CANCELLED", "TIMED_OUT"}:
                    self.ledger.finish(owner, job_id, "cancelled" if status == "CANCELLED" else "failed")
                return public_job(self.ledger.get(owner, job_id))
            if method == "POST" and operation == "/retry":
                # This endpoint never starts a billed task. Original private
                # prompts are not retained in the control ledger.
                return {"submitted": False, "retry_allowed": row["state"] in {"failed", "cancelled", "rejected", "resolved"},
                        "new_request_required": True, "new_idempotency_key_required": True,
                        "instruction": "Review the prior result, then explicitly resubmit the original chat request. Unknown jobs require reconciliation first."}
        raise ControlError("not_found", "Backend resource not found.")

    async def stream_events(self, owner, job_id, after=0, max_seconds=25):
        if type(after) is not int or after < 0:
            raise ControlError("invalid_cursor", "Invalid event cursor.")
        self.ledger.get(owner, job_id)
        started = asyncio.get_running_loop().time()
        while asyncio.get_running_loop().time() - started < max_seconds:
            events = self.ledger.events(owner, job_id, after)
            for event in events:
                after = event["id"]
                yield f"id: {after}\nevent: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            row = self.ledger.get(owner, job_id)
            if row["state"] in {"completed", "failed", "cancelled", "rejected", "resolved"} and not events:
                return
            yield ": heartbeat\n\n"
            await asyncio.sleep(1)


def install_api(app):
    """Register once per app process. Never changes existing app routes or defaults."""
    app.state.family_control_api_active = True
    if getattr(app.state, "family_control_api_installed", False):
        return
    from fastapi import APIRouter, Depends, HTTPException, Request
    from fastapi.responses import JSONResponse, StreamingResponse
    from open_webui.utils.auth import get_verified_user

    async def provider_call(method, endpoint, operation):
        import aiohttp
        from open_webui.models.tools import Tools
        if endpoint not in ENDPOINT_CAPABILITIES or not re.fullmatch(r"health|(?:status|cancel)/[A-Za-z0-9_-]+", operation):
            raise ControlError("invalid_provider_request", "Provider route is not approved.")
        key = await configured_runpod_key()
        if not key:
            raise ControlError("provider_unavailable", "The admin must configure the existing tool credential.")
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), trust_env=True,
                    headers={"Authorization": f"Bearer {key}"}) as session:
                async with session.request(method, f"https://api.runpod.ai/v2/{endpoint}/{operation}") as response:
                    if response.status >= 400:
                        raise ControlError("provider_unavailable", "Provider status or cancellation could not be confirmed.")
                    data = await response.json()
                    if not isinstance(data, dict):
                        raise ControlError("provider_unavailable", "Provider returned an invalid status response.")
                    return data
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            raise ControlError("provider_unavailable", "Provider status or cancellation could not be confirmed.") from None

    api = ControlAPI(provider_call=provider_call)
    router = APIRouter(prefix="/api/v1/family", tags=["Family AI control"])

    async def dispatch(request: Request, user=Depends(get_verified_user)):
        if not app.state.family_control_api_active:
            raise HTTPException(503, "Family backend is disabled")
        path = request.url.path.removeprefix("/api/v1/family")
        body = {}
        if request.method == "POST":
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > 65536:
                    raise HTTPException(413, "Control request too large")
            try:
                body = json.loads(data or b"{}")
            except ValueError:
                raise HTTPException(400, "Invalid JSON") from None
            if not isinstance(body, dict):
                raise HTTPException(400, "A JSON object is required")
        try:
            result = await api.dispatch(request.method, path, {"id": user.id, "role": user.role}, body, dict(request.headers))
            return JSONResponse(result, headers={"Cache-Control": "private, no-store"} if path == "/account" else None)
        except ControlError as error:
            status = 404 if error.code == "not_found" else 403 if error.code in {"forbidden", "origin_forbidden", "origin_required"} else 400
            return JSONResponse({"error": {"code": error.code, "message": str(error)}}, status_code=status)

    async def events(job_id: str, request: Request, user=Depends(get_verified_user)):
        if not app.state.family_control_api_active:
            raise HTTPException(503, "Family backend is disabled")
        try:
            after = int(request.headers.get("last-event-id", request.query_params.get("after", "0")))
            api.ledger.get(user.id, job_id)
            if after < 0:
                raise ValueError()
        except (ControlError, ValueError):
            raise HTTPException(404, "Job or cursor not found") from None
        return StreamingResponse(api.stream_events(user.id, job_id, after), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # Native plugin exec() inherits postponed annotations; Request is a local
    # import here, so FastAPI cannot resolve its string through module globals.
    # Bind the concrete type before it builds dependencies for these routes.
    dispatch.__annotations__["request"] = Request
    events.__annotations__["request"] = Request
    router.add_api_route("/jobs/{job_id}/events", events, methods=["GET"])
    for path, methods in [("/usage", ["GET"]), ("/account", ["GET"]), ("/jobs", ["GET"]), ("/capabilities", ["GET"]), ("/models/state", ["GET"]),
                          ("/policy", ["GET", "POST"]), ("/quote", ["POST"]),
                          ("/billing", ["POST"]), ("/reconciliation", ["GET"]), ("/voice/session", ["GET", "DELETE"]),
                          ("/jobs/{job_id}", ["GET"]), ("/jobs/{job_id}/cancel", ["POST"]),
                          ("/jobs/{job_id}/refresh", ["POST"]),
                          ("/jobs/{job_id}/retry", ["POST"]), ("/jobs/{job_id}/resolve", ["POST"])]:
        router.add_api_route(path, dispatch, methods=methods)
    install_speech_api(app, router, check_origin)
    # Native Open WebUI already mounted its SPA at '/' before lifecycle Events
    # run. Appending routes after that Mount silently serves HTML/405 instead.
    original_routes = list(app.router.routes)
    app.include_router(router)
    added_routes = app.router.routes[len(original_routes):]
    from starlette.routing import Mount
    fallback_index = next((index for index, route in enumerate(original_routes)
                           if isinstance(route, Mount) and route.path in {"", "/"}), len(original_routes))
    app.router.routes[:] = original_routes[:fallback_index] + added_routes + original_routes[fallback_index:]
    app.openapi_schema = None
    app.state.family_control_api_installed = True
