import requests
import logging
from dateutil import parser
import google.oauth2.credentials
import googleapiclient.discovery
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, \
                    InlineKeyboardMarkup, ParseMode, ReplyKeyboardRemove
from telegram.ext import ConversationHandler
from webapp.utils import is_authorized, credentials_to_dict, \
        build_google_api_obj, get_default_calendar_from_db, find_time, \
        extract_date
from webapp.db import mongo
import config
import datetime


logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG,
                    )
logger = logging.getLogger(__name__)

my_keyboard = ReplyKeyboardMarkup([
                                ['Посмотреть расписание'],
                                ['Создать мероприятие'],
                                ['Выбрать календарь по умолчанию']
                                ],
                                resize_keyboard=True
                                )


def start(update, context):
    text = 'Привет!\n Чтобы начать использовать бота, авторизуйся в google /google_auth\n' \
            + 'Чтобы выбрать календарь по умолчанию, используй /google_set_default_calendar\n'\
            + 'Чтобы отозвать разрешение на использование гугл аккаунта, используй /google_revoke\n' \

    update.message.reply_text(text)


def google_auth(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is True:
        text = "Ты уже авторизована. Если хочешь отозвать авторизацию, \
            используй /google_revoke"
        update.message.reply_text(text)
    else:
        auth_url = "https://botorganizer2019.herokuapp.com/auth/{}".format(
                                                    # current_app.config[
                                                    #     'HEROKU_APP_NAME'
                                                    #     ],
                                                    update.message.chat_id
                                                    )
        keyboard = [
                    [InlineKeyboardButton(
                        'Нажми на ссылку, чтобы авторизоваться в гугле',
                        url=auth_url)]
                    ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            'Авторизоваться в google', reply_markup=reply_markup
            )


def help(update, context):
    text = 'Чтобы начать использование бота, введи /start\n' \
        + 'Чтобы просмотреть расписание, используй /check_agenda\n' \
        + 'Чтобы добавить событие, используй /add_event\n' \
        + 'Чтобы пройти авторизацию в гугле, используй /google_auth\n' \
        + 'Чтобы отозвать разрешение на использование гугл аккаунта, используй /google_revoke\n' \
        + 'Чтобы выбрать календарь по умолчанию, используй /google_set_default_calendar\n'
    update.message.reply_text(text)


def google_revoke(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is False:
        text = "Ты не авторизована. Если хочешь пройти авторизацию, \
            используй /google_auth"
        update.message.reply_text(text)
    else:
        # Load credentials
        user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(update.message.chat_id)}
            )
        user_credentials_dict = credentials_to_dict(user_credentials_from_db)
        credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
        revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
                        params={'token': credentials.token},
                        headers={
                            'content-type': 'application/x-www-form-urlencoded'
                                })
        status_code = getattr(revoke, 'status_code')
        if status_code == 200:
            mongo.db.google_credentials.find_one_and_delete(
                    {'_id': str(update.message.chat_id)}
                )
            text = 'Разрешение на доступ к календарю отозвано'
            update.message.reply_text(text)
        else:
            text = 'Произошла ошибка, пожалуйста, напишите на почту lad.shada@gmail.com'
            update.message.reply_text(text)


def check_agenda(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is False:
        text = "Сначала нужно авторизоваться в гугле.\n" \
            + "Для этого используй команду /google_auth"
        update.message.reply_text(text)
    else:
        # Load credentials
        user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(update.message.chat_id)}
            )
        calendar_id = user_credentials_from_db['default_calendar']
        if calendar_id is None:
            print("CALENDAR IDDDDD ", calendar_id)
            update.message.reply_text("Сначала выбери календарь по умолчанию")
        else:
            user_credentials_dict = credentials_to_dict(user_credentials_from_db)
            credentials = google.oauth2.credentials.Credentials(
                **user_credentials_dict)
            calendar = googleapiclient.discovery.build(
                config.API_SERVICE_NAME,
                config.API_VERSION,
                credentials=credentials)
            # calendar = build_google_api_obj(id=update.message.chat_id)
            # logger.INFO(calendar)
            # calendar_id = get_default_calendar_from_db()
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            events_result = calendar.events().list(
                                            calendarId=calendar_id,
                                            timeMin=now,
                                            maxResults=10,
                                            singleEvents=True,
                                            orderBy='startTime').execute()
            events = events_result.get('items', [])
            calendars = calendar.calendarList().list().execute()
            for item in calendars['items']:
                if item['id'] == calendar_id:
                    calendar_name = item['summary']
            text = ''
            if not events:
                text = 'У вас нет предстоящих событий в календаре'
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                start_time = parser.parse(start).strftime("%d %B %Y %H:%M")
                text = text + start_time + ' ' + event['summary'] + '\n'
            update.message.reply_text(
                f'*События из календаря {calendar_name}*\n{text}',
                parse_mode=ParseMode.MARKDOWN
                )


def add_event(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is False:
        text = "Сначала нужно авторизоваться в гугле.\nДля этого используй команду /google_auth"
        update.message.reply_text(text)
    else:
        user_text = update.message.text[11:]
        event_date = extract_date(user_text)
        year, day, month, hour, minute = event_date
        # # Load credentials
        user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(update.message.chat_id)}
            )
        calendar_id = user_credentials_from_db['default_calendar']
        user_credentials_dict = credentials_to_dict(user_credentials_from_db)
        credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
        calendar = googleapiclient.discovery.build(
            config.API_SERVICE_NAME,
            config.API_VERSION,
            credentials=credentials)

        # # Create data for event
        # current_date = datetime.datetime.now().date()
        # tomorrow = datetime.datetime(
        #     current_date.year, current_date.month, current_date.day, 10) + \
        #     datetime.timedelta(days=1)
        event_start = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))
        #event_start = tomorrow.isoformat()
        event_end = (event_start + datetime.timedelta(hours=1)).isoformat()
        event_start = event_start.isoformat()
        event_result = calendar.events().insert(calendarId=calendar_id,
                        body={
                            "summary": user_text,
                            "description": "This event has been created by telegram bot",
                            "start": {
                                "dateTime": event_start,
                                "timeZone": 'GMT+03:00'
                                },
                            "end": {
                                "dateTime": event_end,
                                "timeZone": 'GMT+03:00'
                                },
                        }).execute()
        calendars = calendar.calendarList().list().execute()
        for item in calendars['items']:
            if item['id'] == calendar_id:
                calendar_name = item['summary']
        # print("created event")
        # print("id: ", event_result['id'])
        print("summary: ", event_result['summary'])
        # print("starts at: ", event_result['start']['dateTime'])
        # print("ends at: ", event_result['end']['dateTime'])
        update.message.reply_text(
            'Событие {} создано в календаре {}'.format(event_result['summary'], calendar_name)
            )


def google_set_default_calendar(update, context):
    user_auth_check = is_authorized(update.message.chat_id)
    if user_auth_check is False:
        text = "Сначала нужно авторизоваться в гугле. \
            Для этого используй команду /google_auth"
        update.message.reply_text(text)
    else:
        # Load credentials
        user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(update.message.chat_id)}
            )
        user_credentials_dict = credentials_to_dict(user_credentials_from_db)
        credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
        calendar = googleapiclient.discovery.build(
            config.API_SERVICE_NAME,
            config.API_VERSION,
            credentials=credentials)
        calendars = calendar.calendarList().list().execute()
        keyboard = []
        for item in calendars['items']:
            keyboard.append(
                    [
                        InlineKeyboardButton(
                            item['summary'],
                            callback_data=str(item['id'])
                            )
                    ]
                    )
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            'Выбери календарь, который хочешь назначить по умолчанию',
            reply_markup=reply_markup
            )


def button(update, context):
    query = update.callback_query
    calendar_id = query.data
    mongo.db.google_credentials.find_one_and_update(
                {'_id': str(update.callback_query.message.chat_id)},
                {'$set': {'default_calendar': query.data}}
        )
    user_credentials_from_db = mongo.db.google_credentials.find_one(
            {'_id': str(query.message.chat_id)}
            )
    user_credentials_dict = credentials_to_dict(user_credentials_from_db)
    credentials = google.oauth2.credentials.Credentials(
            **user_credentials_dict)
    calendar = googleapiclient.discovery.build(
            config.API_SERVICE_NAME,
            config.API_VERSION,
            credentials=credentials)
    calendars = calendar.calendarList().list().execute()
    for item in calendars['items']:
        if item['id'] == calendar_id:
            calendar_name = item['summary']
    query.edit_message_text(
          text="Календарь {} установлен по умолчанию".format(calendar_name)
          )


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
