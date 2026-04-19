"""Notification system for batchmark benchmark events."""
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from batchmark.runner import BatchResult


@dataclass
class NotificationEvent:
    label: str
    mean: float
    success_rate: float
    message: str
    level: str = "info"  # info | warn | error


@dataclass
class NotifierConfig:
    min_success_rate: float = 0.0
    max_mean_ms: Optional[float] = None
    on_event: Optional[Callable[[NotificationEvent], None]] = None


def _success_rate(result: BatchResult) -> float:
    if not result.times:
        return 0.0
    return result.success_count / len(result.times)


def evaluate(result: BatchResult, config: NotifierConfig) -> List[NotificationEvent]:
    events: List[NotificationEvent] = []
    rate = _success_rate(result)
    mean_val = sum(result.times) / len(result.times) if result.times else 0.0

    if rate < config.min_success_rate:
        events.append(NotificationEvent(
            label=result.label,
            mean=mean_val,
            success_rate=rate,
            message=f"Success rate {rate:.0%} below threshold {config.min_success_rate:.0%}",
            level="error",
        ))

    if config.max_mean_ms is not None and mean_val > config.max_mean_ms:
        events.append(NotificationEvent(
            label=result.label,
            mean=mean_val,
            success_rate=rate,
            message=f"Mean {mean_val:.1f}ms exceeds max {config.max_mean_ms:.1f}ms",
            level="warn",
        ))

    return events


def notify(results: List[BatchResult], config: NotifierConfig) -> List[NotificationEvent]:
    all_events: List[NotificationEvent] = []
    for result in results:
        events = evaluate(result, config)
        all_events.extend(events)
        if config.on_event:
            for e in events:
                config.on_event(e)
    return all_events
