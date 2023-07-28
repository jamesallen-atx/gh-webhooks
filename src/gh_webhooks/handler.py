import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Dict, List, Union, Optional

from typing_extensions import Protocol, runtime_checkable

from gh_webhooks.resolve_event import resolve_event
from gh_webhooks.types import Model

from gh_webhooks.base import GhWebhooksModel


@runtime_checkable
class _EventHandler(Protocol):
    def __call__(self, event: Model) -> Awaitable[None]:
        ...  # pragma: no cover


@dataclass
class GhWebhookEventHandler:
    """
    An engine for handling GitHub webhook events.
    """

    _ons: Dict[Union[Model, GhWebhooksModel], List[_EventHandler]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def on(self, event_type: Union[Model, GhWebhooksModel]):
        """
        Register a function to handle events of a given type
        """

        def register_event_handler(func: _EventHandler):
            self._ons[event_type].append(func)

        return register_event_handler

    async def handle_event(self, event: Dict[str, Any], kind: Optional[str]):
        """
        Handle a GitHub webhook event JSON, concurrently calling all functions
        registered to that event type.

        ``kind`` is provided by the ``X-Github-Event`` header

        Raises
        ------
        gh_webhooks.exceptions.NoMatchingModel
            If the event can't be matched to a model
        """
        resolved = resolve_event(event, kind)
        return await asyncio.gather(*[fn(resolved) for fn in self._ons[type(resolved)]])  # type: ignore
