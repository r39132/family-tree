from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from google.cloud import firestore

from .deps import get_current_username
from .firestore_client import get_db
from .models import EventNotificationSettings, EventsResponse, FamilyEvent
from .routes_auth import send_mail

router = APIRouter(prefix="/events", tags=["events"])


def calculate_age(birth_date: str, current_date: datetime) -> int:
    """Calculate age on a given date."""
    try:
        # Try multiple date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                birth = datetime.strptime(birth_date, fmt)
                break
            except ValueError:
                continue
        else:
            return 0

        age = current_date.year - birth.year
        # Adjust if birthday hasn't occurred this year yet
        if current_date.month < birth.month or (
            current_date.month == birth.month and current_date.day < birth.day
        ):
            age -= 1
        return max(0, age)
    except ValueError:
        return 0


def parse_date(date_str: str) -> datetime:
    """Parse date string with multiple format support."""
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")


def get_all_year_events(
    members: List[dict], year: int | None = None
) -> tuple[List[FamilyEvent], List[FamilyEvent]]:
    """Get all family events for a given year, split into upcoming and past events."""
    if year is None:
        year = datetime.now().year

    events = []
    today = datetime.now()

    for member in members:
        if not member.get("dob"):
            continue

        try:
            # Parse original date with multiple format support
            original_date = parse_date(member["dob"])

            # Calculate this year's occurrence
            this_year_date = original_date.replace(year=year)

            # Birthday event
            age_on_birthday = calculate_age(member["dob"], this_year_date)
            events.append(
                FamilyEvent(
                    id=f"birthday_{member['id']}_{year}",
                    member_id=member["id"],
                    member_name=f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    event_type="birthday",
                    event_date=this_year_date.strftime("%Y-%m-%d"),
                    age_on_date=age_on_birthday,
                    original_date=member["dob"],
                )
            )

            # Death anniversary if deceased
            if member.get("is_deceased"):
                # For death anniversary, we need a death date - for now use dob as placeholder
                # In a real app, you'd have a separate death_date field
                death_anniversary_date = this_year_date  # Simplified for demo
                years_since_death = year - original_date.year

                events.append(
                    FamilyEvent(
                        id=f"death_anniversary_{member['id']}_{year}",
                        member_id=member["id"],
                        member_name=f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                        event_type="death_anniversary",
                        event_date=death_anniversary_date.strftime("%Y-%m-%d"),
                        age_on_date=years_since_death,
                        original_date=member["dob"],
                    )
                )

        except ValueError:
            # Skip members with invalid date formats
            continue

    # Sort by date
    events.sort(key=lambda x: x.event_date)

    # Split into upcoming and past
    upcoming = [e for e in events if datetime.strptime(e.event_date, "%Y-%m-%d") >= today]
    past = [e for e in events if datetime.strptime(e.event_date, "%Y-%m-%d") < today]

    # Sort past events in reverse chronological order (most recent first)
    past.sort(key=lambda x: x.event_date, reverse=True)

    return upcoming, past


@router.get("/", response_model=EventsResponse)
def get_events(current_user: str = Depends(get_current_username)):
    """Get all family events for this year and notification settings."""
    db = get_db()

    # Get all members from the tree
    members_ref = db.collection("members")
    members = [doc.to_dict() | {"id": doc.id} for doc in members_ref.stream()]

    # Get all events for this year
    upcoming_events, past_events = get_all_year_events(members)

    # Get notification settings for current user
    settings_ref = db.collection("event_notifications").document(current_user)
    settings_doc = settings_ref.get()
    notification_enabled = (
        settings_doc.to_dict().get("enabled", False) if settings_doc.exists else False
    )

    return EventsResponse(
        upcoming_events=upcoming_events,
        past_events=past_events,
        notification_enabled=notification_enabled,
    )


@router.post("/notifications/settings")
def update_notification_settings(
    settings: EventNotificationSettings, current_user: str = Depends(get_current_username)
):
    """Update event notification settings for the current user."""
    db = get_db()

    settings_ref = db.collection("event_notifications").document(current_user)
    settings_ref.set(
        {
            "enabled": settings.enabled,
            "user_id": current_user,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )

    return {"ok": True, "enabled": settings.enabled}


@router.post("/notifications/send-reminders")
def send_event_reminders():
    """Send email reminders for events happening within 48 hours (typically called by a cron job)."""
    db = get_db()

    # Get all users with notifications enabled
    notifications_ref = db.collection("event_notifications").where("enabled", "==", True)
    enabled_users = {doc.id: doc.to_dict() for doc in notifications_ref.stream()}

    if not enabled_users:
        return {"ok": True, "sent": 0, "message": "No users have notifications enabled"}

    # Get all members
    members_ref = db.collection("members")
    members = [doc.to_dict() | {"id": doc.id} for doc in members_ref.stream()]

    # Get events happening in next 2 days
    upcoming_events, _ = get_all_year_events(members)
    today = datetime.now()
    near_future = today + timedelta(days=2)

    # Filter to events within 48 hours
    imminent_events = [
        event
        for event in upcoming_events
        if today <= datetime.strptime(event.event_date, "%Y-%m-%d") <= near_future
    ]

    sent_count = 0

    for user_id in enabled_users:
        # Get user email
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()
        if not user_doc.exists:
            continue

        user_data = user_doc.to_dict()
        user_email = user_data.get("email")
        if not user_email:
            continue

        if imminent_events:
            # Compose email
            subject = f"Family Events Reminder - {len(imminent_events)} upcoming"

            body_lines = ["Hello! Here are the upcoming family events:\n"]
            for event in imminent_events:
                event_date = datetime.strptime(event.event_date, "%Y-%m-%d")
                formatted_date = event_date.strftime("%B %d, %Y")

                if event.event_type == "birthday":
                    body_lines.append(
                        f"🎂 {event.member_name}'s birthday - {formatted_date} (turning {event.age_on_date})"
                    )
                else:
                    body_lines.append(
                        f"🕊️ {event.member_name}'s remembrance - {formatted_date} ({event.age_on_date} years)"
                    )

            body_lines.append("\nBest regards,\nFamily Tree")
            body = "\n".join(body_lines)

            try:
                send_mail(user_email, subject, body)
                sent_count += 1
            except Exception as e:
                print(f"Failed to send email to {user_email}: {e}")

    return {"ok": True, "sent": sent_count, "events": len(imminent_events)}
