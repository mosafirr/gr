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

from typing import Optional

from telegram import Message, Update, ParseMode, Chat
from telegram.ext.callbackcontext import CallbackContext

from haruka import CONFIG
from haruka.modules.disable import DisableAbleCommandHandler
from haruka.modules.helper_funcs.string_handling import remove_emoji
from haruka.modules.tr_engine.strings import tld

from googletrans import LANGUAGES, Translator


def do_translate(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if msg.reply_to_message:
        to_translate_text = remove_emoji(msg.reply_to_message.text)
    else:
        msg.reply_text(tld(chat.id, "translator_no_str"))
        return

    if not args:
        msg.reply_text(tld(chat.id, 'translator_no_args'))
        return
    lang = args[0]

    translator = Translator()
    try:
        translated = translator.translate(to_translate_text, dest=lang)
    except ValueError as e:
        msg.reply_text(tld(chat.id, 'translator_err').format(e))
        return

    src_lang = LANGUAGES[f'{translated.src.lower()}'].title()
    dest_lang = LANGUAGES[f'{translated.dest.lower()}'].title()
    translated_text = translated.text
    msg.reply_text(tld(chat.id,
                       'translator_translated').format(src_lang,
                                                       to_translate_text,
                                                       dest_lang,
                                                       translated_text),
                   parse_mode=ParseMode.MARKDOWN)


__help__ = True

CONFIG.dispatcher.add_handler(
    DisableAbleCommandHandler("tr",
                              do_translate,
                              pass_args=True,
                              run_async=True))
