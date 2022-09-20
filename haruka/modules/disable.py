#    Haruka Aya (A telegram bot project)
#    Copyright (C) 2017-2019 Paul Larsen
#    Copyright (C) 2019-2021 Akito Mizukito (Haruka Aita)

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Union

from future.utils import string_types
from telegram import ParseMode, Update
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.callbackcontext import CallbackContext
from telegram.utils.helpers import escape_markdown

from haruka import CONFIG
from haruka.modules.helper_funcs.handlers import CMD_STARTERS
from haruka.modules.helper_funcs.misc import is_module_loaded

from haruka.modules.tr_engine.strings import tld

FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):
    from haruka.modules.helper_funcs.chat_status import user_admin, is_user_admin

    from haruka.modules.sql import disable_sql as sql

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    class DisableAbleCommandHandler(CommandHandler):
        def __init__(self,
                     command,
                     callback,
                     run_async=False,
                     admin_ok=False,
                     **kwargs):
            super().__init__(command, callback, run_async=run_async, **kwargs)
            self.admin_ok = admin_ok
            if isinstance(command, string_types):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)

        def check_update(self, update):
            chat = update.effective_chat
            user = update.effective_user

            if super().check_update(update):
                args, filter_result = super().check_update(update)

                if not filter_result:
                    return False

                # Should be safe since check_update passed.
                command = update.effective_message.text_html.split(
                    None, 1)[0][1:].split('@')[0]

                # disabled, admincmd, user admin
                if sql.is_command_disabled(chat.id, command):
                    is_admin = command in ADMIN_CMDS and is_user_admin(
                        chat, user.id)
                    if not is_admin:
                        return None

                    return args, is_admin

                return args, filter_result

            return False

    class DisableAbleMessageHandler(MessageHandler):
        def __init__(self,
                     pattern,
                     callback,
                     run_async=False,
                     friendly="",
                     **kwargs):
            super().__init__(pattern, callback, run_async=run_async, **kwargs)
            DISABLE_OTHER.append(friendly or pattern)
            self.friendly = friendly or pattern

        def check_update(self, update):
            if isinstance(update, Update) and update.effective_message:
                chat = update.effective_chat
                return self.filters(update) and not sql.is_command_disabled(
                    chat.id, self.friendly)

    @user_admin
    def disable(update: Update, context: CallbackContext):
        args = context.args
        chat = update.effective_chat
        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, disable_cmd)
                update.effective_message.reply_text(
                    tld(chat.id, "disable_success").format(disable_cmd),
                    parse_mode=ParseMode.MARKDOWN)
            else:
                update.effective_message.reply_text(
                    tld(chat.id, "disable_err_undisableable"))

        else:
            update.effective_message.reply_text(
                tld(chat.id, "disable_err_no_cmd"))

    @user_admin
    def enable(update: Update, context: CallbackContext):
        args = context.args
        chat = update.effective_chat
        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                update.effective_message.reply_text(
                    tld(chat.id, "disable_enable_success").format(enable_cmd),
                    parse_mode=ParseMode.MARKDOWN)
            else:
                update.effective_message.reply_text(
                    tld(chat.id, "disable_already_enabled"))

        else:
            update.effective_message.reply_text(
                tld(chat.id, "disable_err_no_cmd"))

    @user_admin
    def list_cmds(update: Update, context: CallbackContext):
        chat = update.effective_chat
        if DISABLE_CMDS + DISABLE_OTHER:
            result = ""
            for cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                result += " - `{}`\n".format(escape_markdown(cmd))
            update.effective_message.reply_text(tld(
                chat.id, "disable_able_commands").format(result),
                                                parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text(
                tld(chat.id, "disable_able_commands_none"))

    # do not async
    def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return tld(chat_id, "disable_chatsettings_none_disabled")

        result = ""
        for cmd in disabled:
            result += " - `{}`\n".format(escape_markdown(cmd))
        return tld(chat_id,
                   "disable_chatsettings_list_disabled").format(result)

    def commands(update: Update, context: CallbackContext):
        chat = update.effective_chat
        update.effective_message.reply_text(build_curr_disabled(chat.id),
                                            parse_mode=ParseMode.MARKDOWN)

    def __stats__():
        return "• `{}` disabled items, across `{}` chats.".format(
            sql.num_disabled(), sql.num_chats())

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    __help__ = True

    DISABLE_HANDLER = CommandHandler("disable",
                                     disable,
                                     pass_args=True,
                                     run_async=True,
                                     filters=Filters.chat_type.groups)
    ENABLE_HANDLER = CommandHandler("enable",
                                    enable,
                                    pass_args=True,
                                    run_async=True,
                                    filters=Filters.chat_type.groups)
    COMMANDS_HANDLER = CommandHandler(["cmds", "disabled"],
                                      commands,
                                      run_async=True,
                                      filters=Filters.chat_type.groups)
    TOGGLE_HANDLER = CommandHandler("listcmds",
                                    list_cmds,
                                    run_async=True,
                                    filters=Filters.chat_type.groups)

    CONFIG.dispatcher.add_handler(DISABLE_HANDLER)
    CONFIG.dispatcher.add_handler(ENABLE_HANDLER)
    CONFIG.dispatcher.add_handler(COMMANDS_HANDLER)
    # CONFIG.dispatcher.add_handler(TOGGLE_HANDLER)

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleMessageHandler = MessageHandler
