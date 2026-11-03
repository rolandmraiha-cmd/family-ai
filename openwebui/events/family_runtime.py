"""
title: Family AI backend lifecycle
description: Authenticated job, usage and spending-control API; no model warmup.
version: 0.1.0
requirements:
"""

from family_backend.api import install_api


class Event:
    async def event(self, event: dict, __event_name__=None, __app__=None):
        if (__app__ is not None and __event_name__ == "function.disable_started"
                and (event.get("subject") or {}).get("id") == "family_runtime"):
            __app__.state.family_control_api_active = False
            return
        if __app__ is not None and __event_name__ in {
            "system.startup.completed", "function.enabled", "function.updated"
        }:
            install_api(__app__)
