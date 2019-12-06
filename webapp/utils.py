import google.oauth2.credentials
import googleapiclient.discovery
from webapp.db import mongo
from flask import current_app
from natasha import DatesExtractor
import re
from datetime import datetime, timedelta
from pytz import timezone

time_zone = 'Etc/GMT+3'


def credentials_to_dict(credentials):
    return {'token': credentials['token'],
            'refresh_token': credentials['refresh_token'],
            'token_uri': credentials['token_uri'],
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret'],
            'scopes': credentials['scopes'],
            }


def is_authorized(user_id):
    user_str_id = str(user_id)
    result = mongo.db.google_credentials.find_one({'_id': user_str_id})
    if result is not None:
        return True
    else:
        return False


def build_google_api_obj(id):
    user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(id)}
            )
    user_credentials_dict = credentials_to_dict(user_credentials_from_db)
    credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
    calendar = googleapiclient.discovery.build(
            current_app.config.get('API_SERVICE_NAME'),
            current_app.config.get('API_VERSION'),
            credentials=credentials)
    return calendar


def get_default_calendar_from_db(id):
    user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(id)}
            )
    default_calendar_id = user_credentials_from_db['default_calendar']
    return default_calendar_id


def find_time(text):
    hour = None
    minute = None
    if_digit_regexp = r'\d+'
    time_regexp = r'\d{1,2}(:| ){0,1}\d{0,2}'
    day_part_regexp = r'(утром|днем|вечером)'
    day_parts = {'утром': '9:00', 'днем': '13:00', 'вечером': '19:00'}
    is_digit = re.search(if_digit_regexp, text)
    event_time = re.search(time_regexp, text)
    if is_digit is None:
        return None
    else:
        if event_time is None:
            day_part = re.search(day_part_regexp, text)
            if day_part is not None:
                day_part_extracted = day_part.group(0).strip()
                if day_part_extracted in day_parts:
                    hour, minute = day_parts[day_part].split(':')
                return hour, minute
            else:
                return None
        else:
            time = event_time.group(0).strip()
            if ':' in time:
                hour, minute = time.split(':')
                return hour, minute
            elif ' ' in time:
                hour, minute = time.split(' ')
                return hour, minute
            else:
                hour = time
                minute = '00'
                return hour, minute


def extract_date(text):
    year = None
    day = None
    month = None
    text = text.strip()
    extractor = DatesExtractor()
    matches = extractor(text)
    if len(matches.matches) == 0:
        if 'сегодня' in text:
            date = datetime.now(timezone(time_zone))
            day = date.day
            month = date.month
            year = date.year
        elif 'завтра' in text:
            date = datetime.now(timezone(time_zone)) + timedelta(days=1)
            day = date.day
            month = date.month
            year = date.year
        else:
            return "Не могу распознать дату"
    else:
        for match in matches:
            start, stop = match.span
            if match.fact.year is None:
                year = datetime.now().year
                day = match.fact.day
                month = match.fact.month
            else:
                year = match.fact.year
                day = match.fact.day
                month = match.fact.month
            text = re.sub(text[start:stop], '', text)
    time = find_time(text)
    if time is None:
        hour = '00'
        minute = '00'
    else:
        hour, minute = time
    return year, day, month, hour, minute
