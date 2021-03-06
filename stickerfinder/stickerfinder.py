"""A bot which checks if there is a new record in the server section of hetzner."""
import logging
from telegram.ext import (
    Filters,
    CommandHandler,
    CallbackQueryHandler,
    ChosenInlineResultHandler,
    InlineQueryHandler,
    MessageHandler,
    Updater,
)

from stickerfinder.config import config
from stickerfinder.helper import help_text, start_text
from stickerfinder.helper.keyboard import main_keyboard, admin_keyboard
from stickerfinder.helper.session import session_wrapper
from stickerfinder.helper.telegram import call_tg_func
from stickerfinder.telegram.commands import (
    broadcast,
    ban_user,
    unban_user,
    vote_ban_set,
    flag_chat,
    start_tasks,
    tag_single,
    tag_random,
    tag_set,
    cleanup,
    skip,
    cancel,
    stats,
    refresh_sticker_sets,
    refresh_ocr,
    random_set,
    add_sets,
    delete_set,
    set_is_default_language,
    set_not_is_default_language,
)
from stickerfinder.telegram.jobs import (
    newsfeed_job,
    maintenance_job,
    scan_sticker_sets_job,
    distribute_tasks_job,
)
from stickerfinder.telegram.message_handlers import (
    handle_private_text,
    handle_private_sticker,
    handle_group_sticker,
)
from stickerfinder.telegram.callback import (
    handle_callback_query,
    handle_chosen_inline_result,
)
from stickerfinder.telegram.inline_query import search


@session_wrapper()
def start(bot, update, session, chat, user):
    """Send a help text."""
    if chat.is_maintenance or chat.is_newsfeed:
        call_tg_func(update.message.chat, 'send_message', ['Hello there'],
                     {'reply_markup': admin_keyboard})
    else:
        call_tg_func(update.message.chat, 'send_message', [start_text],
                     {'reply_markup': main_keyboard, 'parse_mode': 'HTML'})


def send_help_text(bot, update):
    """Send a help text."""
    call_tg_func(update.message.chat, 'send_message', [help_text],
                 {'reply_markup': main_keyboard, 'parse_mode': 'HTML'})


logging.basicConfig(level=config.LOG_LEVEL,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize telegram updater and dispatcher
updater = Updater(token=config.TELEGRAM_API_KEY, workers=config.WORKER_COUNT,
                  request_kwargs={'read_timeout': 20, 'connect_timeout': 20})

# Create inline query handler
updater.dispatcher.add_handler(InlineQueryHandler(search))

dispatcher = updater.dispatcher
# Create group message handler
dispatcher.add_handler(
    MessageHandler(Filters.sticker & Filters.group, handle_group_sticker))

if not config.LEECHER:
    # Input commands
    dispatcher.add_handler(CommandHandler('tag', tag_single))
    dispatcher.add_handler(CommandHandler('vote_ban', vote_ban_set))
    dispatcher.add_handler(CommandHandler('skip', skip))

    # Button commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', send_help_text))
    dispatcher.add_handler(CommandHandler('tag_set', tag_set))
    dispatcher.add_handler(CommandHandler('tag_random', tag_random))
    dispatcher.add_handler(CommandHandler('random_set', random_set))
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    dispatcher.add_handler(CommandHandler('english', set_is_default_language))
    dispatcher.add_handler(CommandHandler('international', set_not_is_default_language))

    # Maintenance input commands
    dispatcher.add_handler(CommandHandler('ban', ban_user))
    dispatcher.add_handler(CommandHandler('unban', unban_user))
    dispatcher.add_handler(CommandHandler('toggle_flag', flag_chat))
    dispatcher.add_handler(CommandHandler('add_sets', add_sets))
    dispatcher.add_handler(CommandHandler('delete_set', delete_set))
    dispatcher.add_handler(CommandHandler('broadcast', broadcast))

    # Maintenance Button commands
    dispatcher.add_handler(CommandHandler('refresh', refresh_sticker_sets))
    dispatcher.add_handler(CommandHandler('refresh_ocr', refresh_ocr))
    dispatcher.add_handler(CommandHandler('cleanup', cleanup))
    dispatcher.add_handler(CommandHandler('tasks', start_tasks))
    dispatcher.add_handler(CommandHandler('stats', stats))

    # Regular tasks
    job_queue = updater.job_queue
    job_queue.run_repeating(newsfeed_job, interval=60*5, first=0, name='Process newsfeed')
    job_queue.run_repeating(maintenance_job, interval=60*60*24, first=0, name='Create new maintenance tasks')
    job_queue.run_repeating(scan_sticker_sets_job, interval=10, first=0, name='Scan new sticker sets')
    job_queue.run_repeating(distribute_tasks_job, interval=60, first=0, name='Distribute new tasks')

    # Create private message handler
    dispatcher.add_handler(
        MessageHandler(Filters.sticker & Filters.private, handle_private_sticker))
    dispatcher.add_handler(
        MessageHandler(Filters.text & Filters.private, handle_private_text))

    # Inline callback handler
    dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))
    dispatcher.add_handler(ChosenInlineResultHandler(handle_chosen_inline_result))
