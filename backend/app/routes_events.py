from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends
from google.cloud import firestore

from .deps import get_current_username
from .firestore_client import get_db
from .models import EventNotificationSettings, EventsResponse, FamilyEvent
from .routes_auth import send_mail
from .utils.time import utc_now

router = APIRouter(prefix="/events", tags=["events"])


def _get_user_space(username: str) -> str:
    """Get the current space for a user. Returns 'demo' as fallback."""
    db = get_db()
    user_ref = db.collection("users").document(username)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return "demo"  # Default fallback

    data = user_doc.to_dict()
    return data.get("current_space", "demo")


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
        year = utc_now().year

    events = []
    # Use naive datetime for date comparisons since parsed dates are naive
    today = utc_now().date()  # Convert to date for comparison

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
            if member.get("is_deceased") and member.get("date_of_death"):
                try:
                    # Parse the actual death date
                    death_date = parse_date(member["date_of_death"])
                    # Calculate this year's death anniversary
                    death_anniversary_date = death_date.replace(year=year)
                    years_since_death = year - death_date.year

                    events.append(
                        FamilyEvent(
                            id=f"death_anniversary_{member['id']}_{year}",
                            member_id=member["id"],
                            member_name=f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                            event_type="death_anniversary",
                            event_date=death_anniversary_date.strftime("%Y-%m-%d"),
                            age_on_date=years_since_death,
                            original_date=member["date_of_death"],
                        )
                    )
                except ValueError:
                    # Skip if death date is invalid
                    continue

        except ValueError:
            # Skip members with invalid date formats
            continue

    # Sort by date
    events.sort(key=lambda x: x.event_date)

    # Split into upcoming and past
    upcoming = [e for e in events if datetime.strptime(e.event_date, "%Y-%m-%d").date() >= today]
    past = [e for e in events if datetime.strptime(e.event_date, "%Y-%m-%d").date() < today]

    # Sort past events in reverse chronological order (most recent first)
    past.sort(key=lambda x: x.event_date, reverse=True)

    return upcoming, past


@router.get("/", response_model=EventsResponse)
def get_events(current_user: str = Depends(get_current_username)):
    """Get all family events for this year and notification settings."""
    db = get_db()
    space_id = _get_user_space(current_user)

    # Get all members from the current space
    members_ref = db.collection("members")
    members = [
        doc.to_dict() | {"id": doc.id}
        for doc in members_ref.where("space_id", "==", space_id).stream()
    ]

    # Get all events for this year
    upcoming_events, past_events = get_all_year_events(members)

    # Get notification settings for current user in current space
    settings_ref = db.collection("event_notifications").document(f"{current_user}_{space_id}")
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
    settings: EventNotificationSettings,
    current_user: str = Depends(get_current_username),
):
    """Update event notification settings for the current user."""
    db = get_db()
    space_id = _get_user_space(current_user)

    settings_ref = db.collection("event_notifications").document(f"{current_user}_{space_id}")
    settings_ref.set(
        {
            "enabled": settings.enabled,
            "user_id": current_user,
            "space_id": space_id,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )

    return {"ok": True, "enabled": settings.enabled}


@router.post("/notifications/send-reminders")
def send_event_reminders():
    """Send individual email reminders for events happening within 48 hours (typically called by a cron job)."""
    db = get_db()

    # Get all users with notifications enabled (grouped by space)
    notifications_ref = db.collection("event_notifications").where("enabled", "==", True)
    enabled_users = {doc.id: doc.to_dict() for doc in notifications_ref.stream()}

    if not enabled_users:
        return {"ok": True, "sent": 0, "message": "No users have notifications enabled"}

    sent_count = 0
    total_events_processed = 0

    # Group users by space for efficient processing
    users_by_space = {}
    for notification_id, notification_data in enabled_users.items():
        user_id = notification_data.get("user_id")
        space_id = notification_data.get("space_id", "demo")

        if space_id not in users_by_space:
            users_by_space[space_id] = []
        users_by_space[space_id].append((user_id, notification_id))

    # Process each space separately
    for space_id, users_in_space in users_by_space.items():
        # Get all members in this space
        members_ref = db.collection("members")
        members = [
            doc.to_dict() | {"id": doc.id}
            for doc in members_ref.where("space_id", "==", space_id).stream()
        ]

        # Get events happening in next 2 days for this space
        upcoming_events, _ = get_all_year_events(members)
        today = utc_now().date()  # Use date for comparison
        near_future = today + timedelta(days=2)

        # Filter to events within 48 hours (including events happening today)
        imminent_events = [
            event
            for event in upcoming_events
            if today <= datetime.strptime(event.event_date, "%Y-%m-%d").date() <= near_future
        ]

        total_events_processed += len(imminent_events)

        # Send individual notifications to users in this space
        for user_id, notification_id in users_in_space:
            # Get user email and notification settings
            user_ref = db.collection("users").document(user_id)
            user_doc = user_ref.get()
            if not user_doc.exists:
                continue

            user_data = user_doc.to_dict()
            user_email = user_data.get("email")
            if not user_email:
                continue

            # Get when the user enabled notifications to handle late enablers
            notification_settings_ref = db.collection("event_notifications").document(
                notification_id
            )
            notification_settings_doc = notification_settings_ref.get()
            notification_settings = (
                notification_settings_doc.to_dict() if notification_settings_doc.exists else {}
            )

            # Check when notifications were last updated/enabled
            notification_updated_at = notification_settings.get("updated_at")
            recent_enabler = False

            if notification_updated_at:
                # Convert Firestore timestamp to datetime if needed
                if hasattr(notification_updated_at, "seconds"):
                    updated_datetime = datetime.fromtimestamp(
                        notification_updated_at.seconds, tz=timezone.utc
                    )
                else:
                    updated_datetime = notification_updated_at

                # Check if notifications were enabled within the last 6 hours
                # Ensure both datetimes are timezone-aware for comparison
                if updated_datetime.tzinfo is None:
                    updated_datetime = updated_datetime.replace(tzinfo=timezone.utc)

                time_since_enabled = utc_now() - updated_datetime
                recent_enabler = time_since_enabled <= timedelta(hours=6)

            # Send individual emails for each imminent event
            for event in imminent_events:
                # Check if we've already sent a notification for this event to this user
                notification_log_id = (
                    f"{user_id}_{space_id}_{event.member_id}_{event.event_type}_{event.event_date}"
                )
                log_ref = db.collection("event_notification_logs").document(notification_log_id)
                existing_log = log_ref.get()

                if existing_log.exists and not recent_enabler:
                    # Already sent notification for this event, unless user recently enabled notifications
                    continue

                # For recent enablers, check if the event is within 6 hours
                if recent_enabler:
                    event_datetime = datetime.strptime(event.event_date, "%Y-%m-%d")
                    time_until_event = event_datetime.date() - utc_now().date()

                    # Only send to recent enablers if event is within next 6 hours to 48 hours window
                    if time_until_event.days > 2 or (
                        time_until_event.days == 0 and utc_now().hour > 18
                    ):
                        # Skip events that are too far away or events today that have likely passed
                        continue

                # Compose individual email for this event
                event_date = datetime.strptime(event.event_date, "%Y-%m-%d")
                formatted_date = event_date.strftime("%B %d, %Y")

                if event.event_type == "birthday":
                    subject = f"🎂 Upcoming Birthday: {event.member_name}"
                    body = f"""Hello!

This is a reminder that {event.member_name}'s birthday is coming up:

🎂 {event.member_name}'s Birthday
📅 {formatted_date}
🎈 Turning {event.age_on_date} years old

Don't forget to wish them a happy birthday!

Best regards,
Family Tree"""
                else:
                    subject = f"🕊️ Remembrance Day: {event.member_name}"
                    body = f"""Hello!

This is a reminder of an upcoming remembrance day:

🕊️ {event.member_name}'s Remembrance
📅 {formatted_date}
💝 {event.age_on_date} years since they passed

Take a moment to remember and honor their memory.

Best regards,
Family Tree"""

                try:
                    # Send the email
                    send_mail(user_email, subject, body)

                    # Log that we sent this notification (or update existing log for recent enablers)
                    log_ref.set(
                        {
                            "user_id": user_id,
                            "space_id": space_id,
                            "member_id": event.member_id,
                            "event_type": event.event_type,
                            "event_date": event.event_date,
                            "notification_sent_at": utc_now().isoformat(),
                            "created_at": firestore.SERVER_TIMESTAMP,
                            "recent_enabler": recent_enabler,  # Track if this was sent due to recent enabling
                        }
                    )

                    sent_count += 1
                    enabler_msg = " (recent enabler)" if recent_enabler else ""
                    print(
                        f"✅ Sent {event.event_type} notification for {event.member_name} to {user_email}{enabler_msg}"
                    )

                except Exception as e:
                    print(
                        f"❌ Failed to send {event.event_type} notification for {event.member_name} to {user_email}: {e}"
                    )

    return {"ok": True, "sent": sent_count, "events_processed": total_events_processed}


@router.get("/notifications/logs")
def get_notification_logs(current_user: str = Depends(get_current_username), limit: int = 50):
    """Get recent notification logs for the current user's space (for debugging/admin)."""
    db = get_db()
    space_id = _get_user_space(current_user)

    # Get notification logs for this space
    logs_ref = (
        db.collection("event_notification_logs").where("space_id", "==", space_id).limit(limit)
    )

    logs = []
    for doc in logs_ref.stream():
        log_data = doc.to_dict()
        log_data["id"] = doc.id
        logs.append(log_data)

    return {"logs": logs, "space_id": space_id}
