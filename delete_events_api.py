from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta, timezone

SERVICE_ACCOUNT_FILE = 'service_account_key.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'a78836528@gmail.com'

app = Flask(__name__)

def authenticate_service_account():
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=credentials)

def delete_events_on_date(date_str):
    service = authenticate_service_account()
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        time_min = target_date.isoformat()
        time_max = (target_date + timedelta(days=1)).isoformat()

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            return {"message": "No appointments found to delete."}

        for event in events:
            event_id = event['id']
            service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()

        return {"message": "Appointment deleted successfully."}
    except Exception:
        return {"message": "Error occurred while deleting events."}

@app.route('/delete_events', methods=['POST'])
def delete_events():
    data = request.get_json()
    date = data.get('date')

    if not date:
        return jsonify({"message": "Invalid date provided."}), 400

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    result = delete_events_on_date(date)
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
