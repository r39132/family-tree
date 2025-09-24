import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import TopNav from '../components/TopNav';
import { api } from '../lib/api';
import LoadingOverlay from '../components/LoadingOverlay';

type FamilyEvent = {
  id: string;
  member_id: string;
  member_name: string;
  event_type: string;
  event_date: string;
  age_on_date: number;
  original_date: string;
};

type EventsData = {
  upcoming_events: FamilyEvent[];
  past_events: FamilyEvent[];
  notification_enabled: boolean;
};

export default function EventsPage() {
  const router = useRouter();
  const [eventsData, setEventsData] = useState<EventsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<'list' | 'calendar'>('list');
  const [notificationEnabled, setNotificationEnabled] = useState(false);
  const [updatingNotifications, setUpdatingNotifications] = useState(false);

  useEffect(() => {
    loadEvents();
  }, []);

  async function loadEvents() {
    try {
      setLoading(true);
      const data = await api('/events/');
      setEventsData(data);
      setNotificationEnabled(data.notification_enabled);
      setError(null);
    } catch (e: any) {
      if (e.message.includes('401')) {
        router.push('/login');
      } else {
        setError(e.message || 'Failed to load events');
      }
    } finally {
      setLoading(false);
    }
  }

  async function toggleNotifications() {
    try {
      setUpdatingNotifications(true);
      const newEnabled = !notificationEnabled;
      await api('/events/notifications/settings', {
        method: 'POST',
        body: JSON.stringify({ enabled: newEnabled, user_id: '' }) // user_id is set on backend
      });
      setNotificationEnabled(newEnabled);
    } catch (e: any) {
      setError(e.message || 'Failed to update notification settings');
    } finally {
      setUpdatingNotifications(false);
    }
  }

  function formatEventDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  function getEventIcon(eventType: string): string {
    return eventType === 'birthday' ? '🎂' : '🕊️';
  }

  function getEventTypeLabel(eventType: string): string {
    return eventType === 'birthday' ? 'Birthday' : 'Death Anniversary';
  }

  function renderListView() {
    if (!eventsData?.upcoming_events.length && !eventsData?.past_events.length) {
      return (
        <div className="card">
          <p>No events found for this year.</p>
        </div>
      );
    }

    return (
      <>
        {/* Upcoming Events Table */}
        {eventsData.upcoming_events.length > 0 && (
          <div className="card">
            <h3>Upcoming Events ({eventsData.upcoming_events.length})</h3>
            <div className="table-container">
              <table className="events-table">
                <thead>
                  <tr>
                    <th>Person</th>
                    <th>Event Date</th>
                    <th>Event Type</th>
                    <th>Age</th>
                  </tr>
                </thead>
                <tbody>
                  {eventsData.upcoming_events.map((event) => (
                    <tr key={event.id}>
                      <td>
                        <span className="event-icon">{getEventIcon(event.event_type)}</span>
                        {event.member_name}
                      </td>
                      <td>{formatEventDate(event.event_date)}</td>
                      <td>{getEventTypeLabel(event.event_type)}</td>
                      <td>
                        {event.event_type === 'birthday'
                          ? `${event.age_on_date} years old`
                          : `Would be ${event.age_on_date} years old`
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Past Events Table */}
        {eventsData.past_events.length > 0 && (
          <div className="card">
            <h3>Past Events This Year ({eventsData.past_events.length})</h3>
            <div className="table-container">
              <table className="events-table">
                <thead>
                  <tr>
                    <th>Person</th>
                    <th>Event Date</th>
                    <th>Event Type</th>
                    <th>Age</th>
                  </tr>
                </thead>
                <tbody>
                  {eventsData.past_events.map((event) => (
                    <tr key={event.id}>
                      <td>
                        <span className="event-icon">{getEventIcon(event.event_type)}</span>
                        {event.member_name}
                      </td>
                      <td>{formatEventDate(event.event_date)}</td>
                      <td>{getEventTypeLabel(event.event_type)}</td>
                      <td>
                        {event.event_type === 'birthday'
                          ? `Turned ${event.age_on_date}`
                          : `Would be ${event.age_on_date} years old`
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Show message if no events */}
        {eventsData.upcoming_events.length === 0 && eventsData.past_events.length === 0 && (
          <div className="card">
            <p>No events found for this year.</p>
          </div>
        )}
      </>
    );
  }

  function renderCalendarView() {
    const allEvents = [
      ...(eventsData?.upcoming_events || []),
      ...(eventsData?.past_events || [])
    ];

    if (allEvents.length === 0) {
      return (
        <div className="card">
          <p>No events to display in calendar for this year.</p>
        </div>
      );
    }

    // Group events by month
    const eventsByMonth: { [key: string]: FamilyEvent[] } = {};

    allEvents.forEach((event) => {
      const date = new Date(event.event_date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      if (!eventsByMonth[monthKey]) {
        eventsByMonth[monthKey] = [];
      }
      eventsByMonth[monthKey].push(event);
    });

    // Sort months chronologically
    const sortedMonths = Object.keys(eventsByMonth).sort();

    return (
      <div className="calendar-view">
        {sortedMonths.map((monthKey) => {
          const [year, month] = monthKey.split('-');
          const monthName = new Date(parseInt(year), parseInt(month) - 1, 1).toLocaleDateString(undefined, {
            month: 'long',
            year: 'numeric'
          });

          const events = eventsByMonth[monthKey];
          // Sort events within month by date
          events.sort((a, b) => a.event_date.localeCompare(b.event_date));

          return (
            <div key={monthKey} className="card calendar-month">
              <h3>{monthName}</h3>
              <div className="calendar-events">
                {events.map((event) => {
                  const eventDate = new Date(event.event_date);
                  const isPast = eventDate < new Date();

                  return (
                    <div key={event.id} className={`calendar-event ${isPast ? 'past-event' : 'upcoming-event'}`}>
                      <div className="event-date">
                        {eventDate.getDate()}
                      </div>
                      <div className="event-details">
                        <span className="event-icon">{getEventIcon(event.event_type)}</span>
                        <span className="event-name">{event.member_name}</span>
                        <span className="event-type">{getEventTypeLabel(event.event_type)}</span>
                        <span className="event-age">
                          {event.event_type === 'birthday'
                            ? (isPast ? `Turned ${event.age_on_date}` : `Turning ${event.age_on_date}`)
                            : `Would be ${event.age_on_date} years old`
                          }
                        </span>
                        {isPast && <span className="past-indicator">Past</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container">
        <TopNav />
        <div className="card">
          <p>Loading events...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <TopNav />

      <div className="card">
        <div className="events-header">
          <h2>Family Events</h2>

          <div className="events-controls">
            {/* View Toggle */}
            <div className="view-toggle">
              <label>View:</label>
              <select
                value={view}
                onChange={(e) => setView(e.target.value as 'list' | 'calendar')}
                className="input"
              >
                <option value="list">List View</option>
                <option value="calendar">Calendar View</option>
              </select>
            </div>

            {/* Notification Toggle */}
            <div className="notification-toggle">
              <label className="toggle-label" title="Get email reminders 48 hours before events">
                <input
                  type="checkbox"
                  checked={notificationEnabled}
                  onChange={toggleNotifications}
                  disabled={updatingNotifications}
                  className="toggle-checkbox"
                />
                <span className="toggle-slider"></span>
                Email Notifications
              </label>
            </div>
          </div>
        </div>

        {error && (
          <div className="error-message">
            <p style={{ color: 'crimson' }}>{error}</p>
            <button className="btn secondary" onClick={loadEvents}>Retry</button>
          </div>
        )}
      </div>

      {view === 'list' ? renderListView() : renderCalendarView()}

      {/* Loading Overlays */}
      <LoadingOverlay
        isLoading={loading}
        message="Loading family events..."
      />
      <LoadingOverlay
        isLoading={updatingNotifications}
        message="Updating notification settings..."
        transparent={true}
      />
    </div>
  );
}
