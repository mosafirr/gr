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

import re

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, Update
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram.ext.callbackcontext import CallbackContext

from haruka import CONFIG
from haruka.modules.connection import connected
from haruka.modules.helper_funcs.chat_status import user_admin
from haruka.modules.sql.locales_sql import switch_to_locale, prev_locale
from haruka.modules.tr_engine.strings import tld, LANGUAGES
from haruka.modules.tr_engine.list_locale import list_locales


@user_admin
def locale(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    message = update.effective_message
    if len(args) > 0:
        locale = args[0].lower()
        if locale == 'en-us':
            locale = 'en-US'
        if locale in list_locales:
            if locale in LANGUAGES:
                switch_to_locale(chat.id, locale)
                if chat.type == "private":
                    message.reply_text(
                        tld(chat.id, 'language_switch_success_pm').format(
                            list_locales[locale]))
                else:
                    message.reply_text(
                        tld(chat.id, 'language_switch_success').format(
                            chat.title, list_locales[locale]))
            else:
                text = tld(chat.id, "language_not_supported").format(
                    list_locales[locale])
                text += "\n\n*Currently available languages:*\n"
                for lang in LANGUAGES:
                    locale = list_locales[lang]
                    text += "\n *{}* - `{}`".format(locale, lang)
                message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            text = tld(chat.id, "language_code_not_valid")
            text += "\n\n*Currently available languages:*\n"
            for lang in LANGUAGES:
                locale = list_locales[lang]
                text += "\n *{}* - `{}`".format(locale, lang)
            message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        LANGUAGE = prev_locale(chat.id)
        if LANGUAGE:
            locale = LANGUAGE.locale_name
            native_lang = list_locales[locale]
            message.reply_text(tld(
                chat.id, "language_current_locale").format(native_lang),
                               parse_mode=ParseMode.MARKDOWN)
        else:
            message.reply_text(tld(
                chat.id, "language_current_locale").format("English (US)"),
                               parse_mode=ParseMode.MARKDOWN)


@user_admin
def locale_button(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    lang_match = re.findall(r"en-US|id|ru|es", query.data)
    if lang_match:
        if lang_match[0]:
            switch_to_locale(chat.id, lang_match[0])
            query.answer(text=tld(chat.id, 'language_switch_success_pm').
                         format(list_locales[lang_match[0]]))
        else:
            query.answer(text="Error!", show_alert=True)

    try:
        LANGUAGE = prev_locale(chat.id)
        locale = LANGUAGE.locale_name
        curr_lang = list_locales[locale]
    except Exception:
        curr_lang = "English (US)"

    text = tld(chat.id, "language_select_language")
    text += tld(chat.id, "language_user_language").format(curr_lang)

    conn = connected(update, context, user.id, need_admin=False)

    if conn:
        try:
            chatlng = prev_locale(conn).locale_name
            chatlng = list_locales[chatlng]
            text += tld(chat.id, "language_chat_language").format(chatlng)
        except Exception:
            chatlng = "English (US)"

    text += tld(chat.id, "language_sel_user_lang")

    context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("English (US) 🇺🇸",
                                 callback_data="set_lang_en-US"),
            InlineKeyboardButton("Spanish 🇪🇸", callback_data="set_lang_es")
        ]] + [[
            InlineKeyboardButton("Indonesian 🇮🇩", callback_data="set_lang_id"),
            InlineKeyboardButton("Russian 🇷🇺", callback_data="set_lang_ru")
        ]] + [[
            InlineKeyboardButton(f"{tld(chat.id, 'btn_go_back')}",
                                 callback_data="bot_start")
        ]]))

    # query.message.delete()
    context.bot.answer_callback_query(query.id)


LOCALE_HANDLER = CommandHandler(["set_locale", "locale", "lang", "setlang"],
                                locale,
                                pass_args=True)
locale_handler = CallbackQueryHandler(locale_button, pattern="chng_lang")
set_locale_handler = CallbackQueryHandler(locale_button, pattern=r"set_lang_")

CONFIG.dispatcher.add_handler(LOCALE_HANDLER)
CONFIG.dispatcher.add_handler(locale_handler)
CONFIG.dispatcher.add_handler(set_locale_handler)
