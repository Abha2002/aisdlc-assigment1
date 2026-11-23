"""Natural-language reminder intent handling."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import anthropic
except ImportError:  # pragma: no cover - dependency is declared at runtime
    anthropic = None

from .errors import ModelServiceError
from .prompts import SYSTEM_PROMPT

MODEL_NAME = os.getenv("REMINDER_MODEL", "claude-sonnet-4-20250514")
TEMPERATURE = None
_temperature_value = os.getenv("REMINDER_TEMPERATURE")
if _temperature_value is not None:
    try:
        TEMPERATURE = float(_temperature_value)
    except ValueError:
        TEMPERATURE = None

INTENTS = {"create", "reschedule", "snooze", "clarify", "refuse"}
RECURRENCES = {"none", "daily", "weekly", "monthly"}
FIELDS = (
    "intent",
    "title",
    "datetime",
    "timezone",
    "recurrence",
    "snooze_minutes",
    "target_reminder_id",
    "clarification_question",
    "refusal_reason",
)
HORIZON = timedelta(days=1826)


def _fixed(
    intent: str,
    *,
    title: str | None = None,
    datetime: str | None = None,
    timezone: str | None = None,
    recurrence: str = "none",
    snooze_minutes: int | None = None,
    target_reminder_id: Any | None = None,
    clarification_question: str | None = None,
    refusal_reason: str | None = None,
) -> dict[str, Any]:
    """Build the exact public result shape."""
    return {
        "intent": intent,
        "title": title,
        "datetime": datetime,
        "timezone": timezone,
        "recurrence": recurrence,
        "snooze_minutes": snooze_minutes,
        "target_reminder_id": target_reminder_id,
        "clarification_question": clarification_question,
        "refusal_reason": refusal_reason,
    }


def _clarify(text: str, hindi: bool = False) -> dict[str, Any]:
    question = "I could not determine a clear reminder task and time. Please provide more detail."
    if hindi:
        question = "कृपया याद दिलाने का कार्य और समय स्पष्ट करें."
    if re.search(r"remind|tomorrow|today|at\b|in\s+\d+", text, re.I):
        question = "What task should I remind you about and at what time?"
    if hindi:
        question = "कृपया याद दिलाने का कार्य और समय स्पष्ट करें."
    return _fixed("clarify", clarification_question=question)


def _parse_now(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("now must be a non-empty ISO-8601 string")
    result = datetime.fromisoformat(value.strip())
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("now must include a UTC offset")
    return result


def _zone(name: str) -> ZoneInfo:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("tz must be an IANA timezone")
    try:
        return ZoneInfo(name.strip())
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("tz must be an IANA timezone") from exc


def _named_zone(text: str) -> str | None:
    low = text.lower()
    aliases = (
        ("new york", "America/New_York"),
        ("eastern", "America/New_York"),
        ("los angeles", "America/Los_Angeles"),
        ("pacific", "America/Los_Angeles"),
        ("london", "Europe/London"),
        ("tokyo", "Asia/Tokyo"),
        ("kolkata", "Asia/Kolkata"),
        ("india", "Asia/Kolkata"),
        ("utc", "UTC"),
    )
    for alias, zone in aliases:
        if re.search(rf"\b{re.escape(alias)}(?:\s+time)?\b", low):
            return zone
    match = re.search(r"\b([A-Za-z_]+/[A-Za-z_]+(?:/[A-Za-z_]+)?)\b", text)
    if match:
        candidate = match.group(1)
        try:
            _zone(candidate)
            return candidate
        except ValueError:
            pass
    return None


def _is_hindi(text: str) -> bool:
    return bool(re.search("[\u0900-\u097f]", text))


def _unsupported(text: str) -> bool:
    # GR-1: unsupported actions must be refused rather than represented as reminders.
    low = text.lower()
    patterns = (
        r"\bdelete\b",
        r"\bemail\b",
        r"\bsend\b",
        r"\bmessage\b",
        r"\btext\b",
        r"\btool\b",
        r"\bexecute\b",
        r"\brun\s+(?:a\s+)?code\b",
        r"send[_ -]?email",
        r"delete[_ -]?all",
    )
    return any(re.search(pattern, low) for pattern in patterns)


def _credential_free(text: str) -> str:
    cleaned = re.sub(r"['\"][^'\"]*['\"]", "", text)
    cleaned = re.sub(r"\b(?:password|token|secret|api[_ -]?key)\s*(?:is|=|:)\s*\S+", "", cleaned, flags=re.I)
    return cleaned


def _clock(text: str) -> tuple[int, int] | None:
    match = re.search(
        r"\b(?:at\s*)?([01]?\d|2[0-3])(?::([0-5]\d))?\s*(am|pm)\b",
        text,
        re.I,
    )
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or "0")
        meridiem = match.group(3).lower()
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
        return hour, minute
    match = re.search(r"\b(?:at\s*)?([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    hindi = re.search(r"\b([01]?\d|2[0-3])\s*बजे(?:\s*([0-5]?\d)\s*मिनट)?", text)
    if hindi:
        return int(hindi.group(1)), int(hindi.group(2) or "0")
    if re.search(r"\bevening\b|शाम", text, re.I):
        return 18, 0
    return None


def _relative(text: str) -> timedelta | None:
    low = text.lower()
    match = re.search(r"\b(?:in|after)\s+(\d+)\s*(minutes?|mins?|hours?|hrs?|days?|weeks?)\b", low)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    if unit.startswith("minute") or unit.startswith("min"):
        return timedelta(minutes=amount)
    if unit.startswith("hour") or unit.startswith("hr"):
        return timedelta(hours=amount)
    if unit.startswith("day"):
        return timedelta(days=amount)
    return timedelta(weeks=amount)


def _month(text: str) -> tuple[int, int] | None:
    names = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    match = re.search(
        r"\b([0-3]?\d)\s+(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)(?:\s+(20\d{2}|19\d{2}))?\b",
        text,
        re.I,
    )
    if match:
        return int(match.group(1)), names[match.group(2).lower()]  # type: ignore[index]
    match = re.search(
        r"\b(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+([0-3]?\d)(?:,\s*(20\d{2}|19\d{2}))?\b",
        text,
        re.I,
    )
    if match:
        return int(match.group(2)), names[match.group(1).lower()]  # type: ignore[index]
    return None


def _weekday(text: str) -> int | None:
    days = (
        ("monday", 0),
        ("tuesday", 1),
        ("wednesday", 2),
        ("thursday", 3),
        ("friday", 4),
        ("saturday", 5),
        ("sunday", 6),
    )
    low = text.lower()
    for name, number in days:
        if re.search(rf"\b{name}\b", low):
            return number
    return None


def _recurrence(text: str) -> str:
    # BP-4/INV-8: recurrence is limited to supported create-intent values.
    low = text.lower()
    if re.search(r"\b(?:every\s+day|everyday|daily)\b|हर\s+दिन|रोज", low):
        return "daily"
    if re.search(r"\b(?:every\s+week|weekly)\b|हर\s+सप्ताह", low):
        return "weekly"
    if re.search(r"\b(?:every\s+month|monthly)\b|हर\s+महीने", low):
        return "monthly"
    return "none"


def _title(text: str) -> str:
    cleaned = _credential_free(text)
    cleaned = re.split(r"\b(?:ignore|disregard)\b", cleaned, maxsplit=1, flags=re.I)[0]
    cleaned = re.sub(r"(?i)^.*?\bremind\s+(?:me\s+)?(?:to\s+)?", "", cleaned)
    cleaned = re.sub(r"(?i)^.*?\bin\s+\d+\s+(?:minute|hour|day|week)s?\b\s*(?:remind\s+(?:me\s+)?(?:to\s+)?)?", "", cleaned)
    cleaned = re.sub(r"(?i)\b(?:tomorrow|today|tonight)\b", "", cleaned)
    cleaned = re.sub(r"(?i)\b(?:at\s*)?[0-2]?\d(?::[0-5]\d)?\s*(?:am|pm)\b", "", cleaned)
    cleaned = re.sub(r"\b(?:at\s*)?[01]?\d:[0-5]\d\b", "", cleaned)
    cleaned = re.sub(r"\b(?:on\s*)?[0-3]?\d\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+(?:19|20)\d{2})?\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+[0-3]?\d(?:,\s*(?:19|20)\d{2})?\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\b(?:on\s*)?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", "", cleaned, flags=re.I)
    cleaned = re.sub(
        r"\b(?:this\s+coming|coming|next|this)\b",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(
        r"\b(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\b",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"\b(?:in\s+\d+\s+(?:minutes?|mins?|hours?|hrs?|days?|weeks?)|every\s+(?:day|week|month)|evening)\b", "", cleaned, flags=re.I)
    cleaned = re.sub(
        r"\b(?:New York|Los Angeles|London|Tokyo|Kolkata|India|UTC|"
        r"[A-Za-z_]+/[A-Za-z_]+(?:/[A-Za-z_]+)?)\s*(?:time)?\b",
        "",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"\b(?:morning|afternoon|evening)\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\b(?:to\s+)?(?:remind|me|please)\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"(?i)^\s*to\s+", "", cleaned)
    cleaned = re.sub(r"(?i)\b(?:my|with)\b", "", cleaned)
    if _is_hindi(cleaned):
        cleaned = re.sub(r"\b(?:कल|आज|सुबह|शाम|बजे|की|को|याद|दिलाओ|रिमाइंडर)\b", "", cleaned)
        cleaned = re.sub(r"\b[0-2]?\d(?::[0-5]\d)?\b", "", cleaned)
        match = re.search(r"(दवाई(?:\s+लेने)?|दवा(?:ई)?|मेडिकल|[^\s]+)", cleaned)
        if match:
            cleaned = match.group(1)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(" ,.;:-")
    return cleaned[:200]


def _resolve_datetime(
    text: str,
    now: datetime,
    default_zone: str,
) -> tuple[datetime | None, str | None, str | None]:
    # BP-1/INV-2: resolve all expressions from the caller-supplied instant and
    # enforce the strict future and 1826-day horizon at assembly time.
    zone_name = _named_zone(text) or default_zone
    zone = _zone(zone_name)
    local_now = now.astimezone(zone)
    relative = _relative(text)
    if relative is not None:
        result = (now.astimezone(zone) + relative).replace(microsecond=0)
        return result, zone_name, None

    clock = _clock(text)
    month = _month(text)
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
    year = int(year_match.group(1)) if year_match else local_now.year

    target_date = None
    low = text.lower()
    if re.search(r"\btomorrow\b|कल", text, re.I):
        target_date = local_now.date() + timedelta(days=1)
    elif re.search(r"\btoday\b|आज", text, re.I):
        target_date = local_now.date()
    elif month is not None:
        day, month_number = month
        try:
            target_date = datetime(year, month_number, day).date()
        except ValueError:
            return None, zone_name, "Please provide a valid calendar date."
    elif _weekday(text) is not None:
        weekday = _weekday(text)
        assert weekday is not None
        delta = (weekday - local_now.weekday()) % 7
        if delta == 0:
            delta = 7
        if re.search(r"\b(?:this\s+coming|coming|next)\b", low):
            if re.search(r"\bthis\s+coming\s+(monday)\b", low) and local_now.weekday() == 5:
                delta = 2
        target_date = local_now.date() + timedelta(days=delta)

    if target_date is None:
        if clock is not None:
            target_date = local_now.date()
        elif re.search(r"\bevening\b|शाम", text, re.I):
            target_date = local_now.date()
        else:
            return None, zone_name, "Which date and time should I use?"

    if clock is None:
        if re.search(r"\bevening\b|शाम", text, re.I):
            clock = (18, 0)
        elif re.search(r"\bmorning\b|सुबह", text, re.I):
            clock = (7, 0)
        else:
            return None, zone_name, "What exact time should I use?"

    result = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        clock[0],
        clock[1],
        tzinfo=zone,
    )
    if result <= now:
        if target_date == local_now.date():
            recurrence = _recurrence(text)
            if recurrence == "none":
                result = result + timedelta(days=1)
        else:
            return None, zone_name, "That date or time is in the past. Please choose a future time."
    if result > now + HORIZON:
        return None, zone_name, "That date is beyond the 5-year scheduling horizon. Please choose a sooner date."
    return result, zone_name, None


def _format_datetime(value: datetime) -> str:
    return value.isoformat(timespec="minutes")


def _local_result(
    text: str,
    now: datetime,
    default_zone: str,
    existing_reminders: list[dict[str, Any]],
) -> dict[str, Any]:
    hindi = _is_hindi(text)
    cleaned = _credential_free(text)

    if _unsupported(text):
        reason = "I can only create, reschedule, or snooze reminders."
        if hindi:
            reason = "मैं केवल रिमाइंडर बना, पुनर्निर्धारित या स्नूज़ कर सकता हूं."
        return _fixed("refuse", refusal_reason=reason)

    snooze_match = re.search(r"\bsnooz(?:e|ed|ing)\b|स्नूज़", text, re.I)
    if snooze_match:
        matches = _matching_reminders(text, existing_reminders)
        duration_match = re.search(r"\b(\d{1,4})\s*(?:minutes?|mins?|मिनट)\b", text, re.I)
        if len(matches) != 1:
            question = "Which reminder should I snooze, and for how many minutes?"
            if hindi:
                question = "कौन सा रिमाइंडर और कितने मिनट के लिए स्नूज़ करना है?"
            return _fixed("clarify", clarification_question=question)
        if not duration_match:
            question = "For how many minutes should I snooze this reminder?"
            if hindi:
                question = "कितने मिनट के लिए रिमाइंडर स्नूज़ करना है?"
            return _fixed("clarify", clarification_question=question)
        minutes = int(duration_match.group(1))
        if not 1 <= minutes <= 1440:
            return _fixed(
                "clarify",
                clarification_question="Please choose a snooze duration from 1 to 1440 minutes.",
            )
        return _fixed(
            "snooze",
            snooze_minutes=minutes,
            target_reminder_id=matches[0]["id"],
        )

    reschedule_match = re.search(r"\b(?:move|reschedule|change|shift)\b", text, re.I)
    if reschedule_match:
        matches = _matching_reminders(text, existing_reminders)
        if len(matches) != 1:
            question = "Which reminder should I reschedule?"
            if hindi:
                question = "कौन सा रिमाइंडर पुनर्निर्धारित करना है?"
            return _fixed("clarify", clarification_question=question)
        resolved, zone_name, error = _resolve_datetime(text, now, default_zone)
        if resolved is None:
            question = error or "What future date and time should I use?"
            if hindi:
                question = "कृपया भविष्य की तारीख और समय बताएं."
            return _fixed("clarify", clarification_question=question)
        return _fixed(
            "reschedule",
            datetime=_format_datetime(resolved),
            timezone=zone_name,
            target_reminder_id=matches[0]["id"],
        )

    resolved, zone_name, error = _resolve_datetime(cleaned, now, default_zone)
    if resolved is None:
        if re.search(r"\bremind\b|रिमाइंड|याद", text, re.I):
            title = _title(cleaned)
            if not title:
                question = "What task should I remind you about?"
            elif error:
                question = error
            else:
                question = "What date or time should I use for the reminder?"
            if hindi:
                question = "कृपया याद दिलाने का कार्य और समय बताएं."
            return _fixed("clarify", clarification_question=question[:300])
        return _clarify(text, hindi=hindi)

    title = _title(cleaned)
    if not title:
        question = "What task should I remind you about?"
        if hindi:
            question = "कृपया याद दिलाने का कार्य बताएं."
        return _fixed("clarify", clarification_question=question)
    recurrence = _recurrence(cleaned)
    return _fixed(
        "create",
        title=title,
        datetime=_format_datetime(resolved),
        timezone=zone_name,
        recurrence=recurrence,
    )


def _matching_reminders(
    text: str,
    existing_reminders: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # BP-6/INV-4/INV-5: target IDs come only from exact supplied reminder records.
    low = text.lower()
    matches: list[dict[str, Any]] = []
    for reminder in existing_reminders:
        reminder_id = reminder.get("id")
        title = reminder.get("title")
        if not isinstance(reminder_id, (str, int, float, bool)):
            continue
        if isinstance(title, str) and title.strip():
            words = re.findall(r"[a-z0-9]+", title.lower())
            if title.lower() in low or any(len(word) >= 4 and word in low for word in words):
                matches.append(reminder)
    return matches


def _valid_output_shape(output: Any) -> bool:
    if not isinstance(output, dict):
        return False
    if set(output) != set(FIELDS):
        return False
    if output["intent"] not in INTENTS:
        return False
    if output["recurrence"] not in RECURRENCES:
        return False
    if not isinstance(output["title"], (str, type(None))):
        return False
    if not isinstance(output["datetime"], (str, type(None))):
        return False
    if not isinstance(output["timezone"], (str, type(None))):
        return False
    if output["snooze_minutes"] is not None:
        if isinstance(output["snooze_minutes"], bool):
            return False
        if not isinstance(output["snooze_minutes"], int):
            return False
        if not 1 <= output["snooze_minutes"] <= 1440:
            return False
    if not isinstance(output["clarification_question"], (str, type(None))):
        return False
    if not isinstance(output["refusal_reason"], (str, type(None))):
        return False
    if output["target_reminder_id"] is not None:
        if not isinstance(output["target_reminder_id"], (str, int, float, bool)):
            return False
    if output["title"] is not None and len(output["title"]) > 200:
        return False
    if output["clarification_question"] is not None and len(output["clarification_question"]) > 300:
        return False
    if output["refusal_reason"] is not None and len(output["refusal_reason"]) > 300:
        return False
    return True


def _valid_output_invariants(
    output: dict[str, Any],
    now: datetime,
    existing_reminders: list[dict[str, Any]],
) -> bool:
    intent = output["intent"]
    if intent == "create":
        if not isinstance(output["title"], str) or not output["title"].strip():
            return False
        if output["target_reminder_id"] is not None:
            return False
        if output["datetime"] is None:
            return False
    if intent == "clarify":
        if not isinstance(output["clarification_question"], str):
            return False
        if not output["clarification_question"].strip():
            return False
    if intent == "refuse":
        if not isinstance(output["refusal_reason"], str) or not output["refusal_reason"].strip():
            return False
    if intent in ("clarify", "refuse", "snooze") and output["datetime"] is not None:
        return False
    if intent != "snooze" and output["snooze_minutes"] is not None:
        return False
    if intent != "create" and output["recurrence"] != "none":
        return False
    existing_ids = {item.get("id") for item in existing_reminders if isinstance(item, dict)}
    if intent == "snooze":
        if output["target_reminder_id"] not in existing_ids:
            return False
    if intent == "reschedule":
        if output["target_reminder_id"] not in existing_ids:
            return False
    if intent in ("create", "reschedule"):
        try:
            value = _parse_now(output["datetime"])
        except (TypeError, ValueError):
            return False
        if value <= now or value > now + HORIZON:
            return False
        zone_name = output["timezone"]
        if not isinstance(zone_name, str):
            return False
        try:
            zone = _zone(zone_name)
            return value.astimezone(zone).utcoffset() == value.utcoffset()
        except ValueError:
            return False
    if output["timezone"] is not None:
        try:
            _zone(output["timezone"])
        except ValueError:
            return False
    return True


def _extract_json(content: str) -> dict[str, Any]:
    if not isinstance(content, str):
        raise ValueError("model response must be text")
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError("model response must be a JSON object")
    return value


def _service_error(exc: Exception) -> ModelServiceError:
    message = str(exc).lower()
    if "timeout" in message or "timed out" in message:
        return ModelServiceError("Model request timed out.")
    if "rate" in message and "limit" in message:
        return ModelServiceError("Model service rate limit was reached.")
    if "authentication" in message or "api key" in message:
        return ModelServiceError("The Anthropic API key is invalid or missing.")
    if any(word in message for word in ("network", "connection", "server", "api", "status")):
        return ModelServiceError("Model service API, server, or network failure.")
    return ModelServiceError("Anthropic SDK failure.")


def _call_model(
    text: str,
    now: str,
    tz: str,
    existing_reminders: list[dict[str, Any]],
) -> dict[str, Any]:
    if anthropic is None:
        raise ModelServiceError("Anthropic SDK is unavailable.")
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ModelServiceError("ANTHROPIC_API_KEY is not set.")

    context = json.dumps(
        {
            "text": text,
            "now": now,
            "tz": tz,
            "existing_reminders": existing_reminders,
        },
        ensure_ascii=False,
    )
    parsed_now = _parse_now(now)
    fallback = _fixed(
        "clarify",
        clarification_question="Please clarify the reminder task, time, or target.",
    )
    try:
        client = anthropic.Anthropic(api_key=key)
    except Exception as exc:
        raise _service_error(exc) from exc

    temperature = TEMPERATURE
    for attempt in range(2):
        kwargs: dict[str, Any] = {
            "model": MODEL_NAME,
            "max_tokens": 500,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": context}],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        try:
            response = client.messages.create(**kwargs)
        except Exception as exc:
            message = str(exc).lower()
            if "temperature" in message and "unsupported" in message and attempt == 0:
                temperature = None
                globals()["TEMPERATURE"] = None
                continue
            raise _service_error(exc) from exc

        content = ""
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "text":
                content += getattr(block, "text", "")
        try:
            output = _extract_json(content)
            if not _valid_output_shape(output):
                raise ValueError("invalid output shape")
            if not _valid_output_invariants(output, parsed_now, existing_reminders):
                raise ValueError("invalid output invariants")
            return output
        except (json.JSONDecodeError, TypeError, ValueError):
            if attempt == 0:
                continue
            return fallback
    return fallback


def handle(
    text: str,
    now: str,
    tz: str,
    existing_reminders: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve a reminder request into one fixed JSON-serializable intent object."""
    if not isinstance(text, str) or not text.strip():
        return _fixed(
            "clarify",
            clarification_question="What reminder would you like and when should it happen?",
        )

    try:
        parsed_now = _parse_now(now)
        zone = _zone(tz)
    except (TypeError, ValueError) as exc:
        return _fixed(
            "clarify",
            clarification_question="Please provide a valid reference time and IANA timezone.",
        )

    if existing_reminders is None:
        existing_reminders = []
    if not isinstance(existing_reminders, list):
        return _fixed(
            "clarify",
            clarification_question="Please provide existing reminders as a list.",
        )
    if not all(isinstance(item, dict) for item in existing_reminders):
        return _fixed(
            "clarify",
            clarification_question="Please provide valid existing reminder records.",
        )

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ModelServiceError("ANTHROPIC_API_KEY is not set.")

    # BP-3/INV-3: malformed text, unsupported actions, targets, and missing input
    # are resolved locally so the application never guesses or executes an action.
    unsupported = _unsupported(text)
    has_snooze = bool(re.search(r"\bsnooz(?:e|ed|ing)\b|स्नूज़", text, re.I))
    has_reschedule = bool(re.search(r"\b(?:move|reschedule|change|shift)\b", text, re.I))
    # GR-2/GR-3: embedded instructions and credential literals are contained locally.
    has_injection = bool(re.search(r"\b(?:ignore|disregard)\b.{0,80}\b(?:instruction|previous|system)\b", text, re.I))
    has_credentials = _credential_free(text) != text
    meaningful = bool(re.search(r"[A-Za-z\u0900-\u097f]{3,}", text))
    if (
        unsupported
        or has_snooze
        or has_reschedule
        or has_injection
        or has_credentials
        or not meaningful
    ):
        return _local_result(text, parsed_now, zone.key, existing_reminders)

    # OSC-2/OSC-3/OSC-4: nonblank non-special create requests use the SDK once or
    # one bounded retry, and model-output violations return a fixed safe clarify.
    try:
        return _call_model(text, now, tz, existing_reminders)
    except ModelServiceError:
        raise
