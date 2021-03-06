"""Some functions to cleanup the database."""
from stickerfinder.helper import ignored_characters
from stickerfinder.helper.telegram import call_tg_func
from stickerfinder.helper.keyboard import admin_keyboard
from stickerfinder.models import (
    Tag,
    User,
)


def tag_cleanup(session, update):
    """Do some cleanup tasks for tags."""
    from stickerfinder.helper import blacklist

    all_tags = session.query(Tag).all()
    call_tg_func(update.message.chat, 'send_message', [f'Found {len(all_tags)} tags'])
    for tag in all_tags:
        # Remove all tags in the blacklist
        if tag.name in blacklist:
            session.delete(tag)

            continue

        # Remove ignored characters from tag
        new_name = tag.name
        for char in ignored_characters:
            if char in new_name:
                new_name = new_name.replace(char, '')

        # Remove hash tags
        if new_name.startswith('#'):
            new_name = new_name[1:]

        # If the new tag with removed chars already exists in the db, remove the old tag.
        # Otherwise just update the tag name
        if new_name != tag.name:
            new_exists = session.query(Tag).get(new_name)
            if new_exists is not None or new_name == '':
                session.delete(tag)
            else:
                tag.name = new_name

    call_tg_func(update.message.chat, 'send_message', ['Tag cleanup finished.'], {'reply_markup': admin_keyboard})


def user_cleanup(session, update):
    """Do some cleanup tasks for users."""
    all_users = session.query(User).all()
    deleted = 0
    call_tg_func(update.message.chat, 'send_message', [f'Found {len(all_users)} users'])
    for user in all_users:
        if len(user.changes) == 0 \
                and len(user.tasks) == 0 \
                and len(user.vote_bans) == 0 \
                and len(user.inline_queries) == 0 \
                and user.banned is False \
                and user.reverted is False \
                and user.admin is False \
                and user.authorized is False:
            deleted += 1
            session.delete(user)

    call_tg_func(update.message.chat, 'send_message',
                 [f'User cleanup finished. {deleted} user deleted.'],
                 {'reply_markup': admin_keyboard})
