from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

SERVICE_ACCOUNT_FILE = 'service_account_key.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'a78836528@gmail.com'
TIMEZONE = 'Europe/Brussels'

app = Flask(__name__)

def authenticate_service_account():
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=credentials)

def delete_all_events():
    service = authenticate_service_account()
    try:
        now = datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        if not events:
            return True
        for event in events:
            service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
        return True
    except Exception:
        return False

def create_new_event(date_str, time_str, summary, description):
    service = authenticate_service_account()
    try:
        start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        end_time = start_time + timedelta(hours=1)
        start_time_iso = start_time.isoformat() + "+01:00"
        end_time_iso = end_time.isoformat() + "+01:00"
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time_iso,
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': end_time_iso,
                'timeZone': TIMEZONE,
            },
        }
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return True
    except Exception:
        return False

@app.route('/reschedule_event', methods=['POST'])
def reschedule_event():
    data = request.get_json()
    date = data.get('date')
    time = data.get('time')
    summary = data.get('summary', 'New Event')
    description = data.get('description', 'No description')

    if not date or not time:
        return jsonify({"message": "Invalid date or time."}), 400

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        time_obj = datetime.strptime(time, "%H:%M:%S")
        event_start = datetime.combine(date_obj, time_obj.time())
        event_end = event_start + timedelta(hours=1)
        if event_start.hour < 8 or event_end.hour > 18 or (event_end.hour == 18 and event_end.minute > 0):
            return jsonify({"message": "Invalid time. Appointments must be between 08:00 and 18:00."}), 400
        if date_obj.weekday() > 5:
            return jsonify({"message": "Invalid day. Appointments can only be scheduled from Monday to Saturday."}), 400
    except ValueError:
        return jsonify({"message": "Invalid date or time format."}), 400

    if not delete_all_events():
        return jsonify({"message": "Failed to delete existing appointments."}), 500

    if not create_new_event(date, time, summary, description):
        return jsonify({"message": "Failed to create a new appointment."}), 500

    return jsonify({"message": "Appointment rescheduled successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
