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

def check_event_exists(service, start_time, end_time):
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return len(events_result.get('items', [])) > 0
    except Exception as e:
        return f"Error checking existing events: {str(e)}"

def create_new_event(service, date_str, time_str, summary, description):
    try:
        start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        end_time = start_time + timedelta(hours=1)
        start_time_iso = start_time.isoformat() + "+01:00"
        end_time_iso = end_time.isoformat() + "+01:00"
        if check_event_exists(service, start_time_iso, end_time_iso):
            return {"message": "Appointment already exists"}
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time_iso, 'timeZone': TIMEZONE},
            'end': {'dateTime': end_time_iso, 'timeZone': TIMEZONE},
        }
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return {"message": "New appointment booked"}
    except Exception as e:
        return {"message": f"Error: {str(e)}"}

@app.route('/create_event', methods=['POST'])
def create_event():
    data = request.get_json()
    date = data.get('date')
    time = data.get('time')
    summary = data.get('summary', 'New Event')
    description = data.get('description', 'No description')

    if not date or not time:
        return jsonify({"message": "Invalid request. Provide 'date' (YYYY-MM-DD) and 'time' (HH:MM:SS)."}), 400

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        time_obj = datetime.strptime(time, "%H:%M:%S")
        event_start = datetime.combine(date_obj, time_obj.time())
        event_end = event_start + timedelta(hours=1)
        if event_start.hour < 8 or event_end.hour > 18 or (event_end.hour == 18 and event_end.minute > 0):
            return jsonify({"message": "Appointments must be between 08:00 and 18:00 with a 1-hour duration."}), 400
        if date_obj.weekday() > 5:
            return jsonify({"message": "Appointments can only be scheduled from Monday to Saturday."}), 400
    except ValueError:
        return jsonify({"message": "Invalid date or time format. Use 'YYYY-MM-DD' for date and 'HH:MM:SS' for time."}), 400

    service = authenticate_service_account()
    result = create_new_event(service, date, time, summary, description)

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
