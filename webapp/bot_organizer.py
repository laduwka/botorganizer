from queue import Queue
from threading import Thread
from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler, Filters, MessageHandler, \
                    CallbackQueryHandler, ConversationHandler, RegexHandler
from flask import current_app
from webapp.handlers import start, check_agenda, add_event, help, \
    google_auth, google_set_default_calendar, google_revoke, button, error


def telegram_bot_runner():
    bot = Bot(current_app.config.get('TOKEN'))
    update_queue = Queue()
    dp = Dispatcher(bot, update_queue, use_context=True)

    # add_event_handler = ConversationHandler(
    #     entry_points=[RegexHandler('^(Создать мероприятие)$', add_event)],
    #     states={
    #         'info': [MessageHandler(Filters.text, add_event_info)]
    #     },
    #     fallbacks=[]
    # )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("check_agenda", check_agenda))
    dp.add_handler(CommandHandler("add_event", add_event))
    # dp.add_handler(MessageHandler(
    #     Filters.regex('^(Посмотреть расписание)$'), check_agenda
    #     ))
    # dp.add_handler(MessageHandler(
    #     Filters.regex('^(Создать мероприятие)$'), add_event
    #     ))
    # dp.add_handler(MessageHandler(
    #     Filters.regex('^(Выбрать календарь по умолчанию)$'),
    #     google_set_default_calendar
    #     ))
    # dp.add_handler(add_event_handler)
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('google_auth', google_auth))
    dp.add_handler(CommandHandler(
        'google_set_default_calendar', google_set_default_calendar)
        )
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler('google_revoke', google_revoke))
    dp.add_error_handler(error)

    thread = Thread(target=dp.start, name='dp')
    thread.start()

    return bot, update_queue
