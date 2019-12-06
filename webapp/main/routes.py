from flask import Blueprint, redirect, current_app, request
from telegram import Update
from webapp.bot_organizer import telegram_bot_runner
blueprint = Blueprint('main', __name__, url_prefix='/')


@blueprint.route('/')
def index():
    return redirect(current_app.config['TELEGRAM_BOT_URL'])


@blueprint.route('/<token>', methods=['GET', 'POST'])
def webhook(token):
    if token != current_app.config.get('TOKEN'):
        return 'NOT OK'
    else:
        bot, update_queue = telegram_bot_runner()
        if request.method == "POST":
            # retrieve the message in JSON and then transform it to Telegram object
            update = Update.de_json(request.get_json(force=True), bot)
            update_queue.put(update)
            return "OK"
