from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class DelayedTime:
    planned: datetime
    delay: timedelta

    @classmethod
    def from_iso(cls, planned: str | None, delay: int | None):
        """takes planned in ISO format and delay in minutes"""
        if planned is None:
            return None
        return cls(
            planned=datetime.fromisoformat(planned),
            delay=timedelta(minutes=delay or 0),
        )

    @classmethod
    def from_timestamps(cls, planned: int | None, real: int | None):
        if planned is None:
            return None
        if real is None:
            real = planned
        planned_time = datetime.fromtimestamp(planned, tz=timezone.utc)
        real_time = datetime.fromtimestamp(real, tz=timezone.utc)
        return cls(
            planned=planned_time,
            delay=real_time - planned_time,
        )

    @classmethod
    def from_timestamps_ms(cls, planned: int | None, real: int | None):
        return cls.from_timestamps(
            planned // 1000 if planned is not None else planned,
            real // 1000 if real is not None else real,
        )

    @property
    def real(self):
        return self.planned + self.delay

    def __str__(self):
        time = self.real.strftime("%H:%M")
        if self.delay:
            return (
                f"{time} <sup>{int(round(self.delay / timedelta(minutes=1))):+}</sup>"
            )
        return f"{time}"


@dataclass(frozen=True)
class Stop:
    name: str
    id: str | None = None
    arrival: DelayedTime | None = None
    departure: DelayedTime | None = None
    track: str | None = None

    def __str__(self):
        if self.arrival and self.departure and self.arrival != self.departure:
            time = f"{self.arrival} – {self.departure}"
        elif time_value := self.arrival or self.departure:
            time = str(time_value)
        else:
            time = ""
        return f"{self.name} " + (f"[{self.track}] " if self.track else "") + time


@dataclass(frozen=True)
class Status:
    provider: str
    line: str | None = None
    line_id: str | None = None
    vehicle: str | None = None
    origin: str | None = None
    destination: str | None = None
    wagon_class: str | None = None
    speed: str | None = None

    next_stop: Stop | None = None
    stops: list[Stop] = field(default_factory=list)

    def get_text(self):
        if self.line:
            res = f"󰔬 {self.line} "
        elif self.vehicle and self.line_id:
            res = f"󰔬 {self.vehicle} {self.line_id} "
        elif l := self.vehicle or self.line_id:
            res = f"󰔬 {l} "
        else:
            res = ""

        if self.next_stop:
            res += f"  {self.next_stop} "
        elif self.destination:
            res += f"→ {self.destination} "

        if self.speed:
            res += f"󰓅 {self.speed:.0f}"

        return res.strip()

    def get_tooltip(self):
        lines = []
        # show next stops
        reached_next = False
        for stop in self.stops:
            if stop == self.next_stop:
                reached_next = True
            if reached_next:
                lines.append(str(stop))
        return "\n".join(lines)
