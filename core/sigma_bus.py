import asyncio
from typing import Callable, Dict

class SigmaBus:
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.stats = {"messages_routed": 0, "failures": 0}

    def register_handler(self, domain_tag: str, handler: Callable):
        self.handlers[domain_tag] = handler

    async def route(self, message):
        domain = message.delta
        self.stats["messages_routed"] += 1
        if domain in self.handlers:
            return await self.handlers[domain](message)
        else:
            self.stats["failures"] += 1
            return {"status": "unhandled", "error": "No aperture matches domain."}

    def get_stats(self):
        return self.stats

def create_sigma_bus():
    return SigmaBus()
