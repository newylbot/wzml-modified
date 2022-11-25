from os import remove as osremove, path as ospath, mkdir
from sys import prefix
from PIL import Image
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from time import sleep, time
from functools import partial
from html import escape

from bot import user_data, dispatcher, LOGGER, config_dict, DATABASE_URL
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendPhoto
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.bot_utils import update_user_ldata

handler_dict = {}

def get_user_settings(from_user):
    user_id = from_user.id
    name = from_user.full_name
    buttons = ButtonMaker()
    thumbpath = f"Thumbnails/{user_id}.jpg"
    prefix = user_data[user_id]['prefix'] if user_id in user_data and user_data[user_id].get('prefix') else "Not Exists"
    suffix = user_data[user_id]['suffix'] if user_id in user_data and user_data[user_id].get('suffix') else "Not Exists"
    caption = user_data[user_id]['caption'] if user_id in user_data and user_data[user_id].get('caption') else "Not Exists"
    userlog = user_data[user_id]['userlog'] if user_id in user_data and user_data[user_id].get('userlog') else "Not Exists"
    remname = user_data[user_id]['remname'] if user_id in user_data and user_data[user_id].get('remname') else "Not Exists"
    cfont = user_data[user_id]['cfont'][0] if user_id in user_data and user_data[user_id].get('cfont') else "Not Exists"
    user_dict = user_data.get(user_id, False)
    if not user_dict and config_dict['AS_DOCUMENT'] or user_dict and user_dict.get('as_doc'):
        ltype = "DOCUMENT"
        buttons.sbutton("Send As Media", f"userset {user_id} med")
    else:
        ltype = "MEDIA"
        buttons.sbutton("Send As Document", f"userset {user_id} doc")

    if user_dict and user_dict.get('yt_ql'):
        ytq = user_dict['yt_ql']
        buttons.sbutton("Change/Remove YT-DLP Quality", f"userset {user_id} ytq")
    elif config_dict['YT_DLP_QUALITY']:
        ytq = config_dict['YT_DLP_QUALITY']
        buttons.sbutton("Set YT-DLP Quality", f"userset {user_id} ytq")
    else:
        buttons.sbutton("Set YT-DLP Quality", f"userset {user_id} ytq")
        ytq = 'Not Exists'


    uplan = "Paid User" if user_id in user_data and (user_data[user_id].get('is_paid')) else "Normal User"

    if ospath.exists(thumbpath):
        thumbmsg = "Exists"
        buttons.sbutton("Change/Delete Thumbnail", f"userset {user_id} sthumb")
        buttons.sbutton("Show Thumbnail", f"userset {user_id} showthumb")
    else:
        thumbmsg = "Not Exists"
        buttons.sbutton("Set Thumbnail", f"userset {user_id} sthumb")
    buttxt = "Change/Delete Prefix" if prefix != "Not Exists" else "Set Prefix"
    buttons.sbutton(buttxt, f"userset {user_id} suniversal prefix")
    buttxt = "Change/Delete Suffix" if suffix != "Not Exists" else "Set Suffix"
    buttons.sbutton(buttxt, f"userset {user_id} suniversal suffix")
    buttxt = "Change/Delete Caption" if caption != "Not Exists" else "Set Caption"
    buttons.sbutton(buttxt, f"userset {user_id} suniversal caption")
    buttxt = "Change/Delete UserLog" if userlog != "Not Exists" else "Set UserLog"
    buttons.sbutton(buttxt, f"userset {user_id} suniversal userlog")
    buttxt = "Change/Delete Remname" if remname != "Not Exists" else "Set Remname"
    buttons.sbutton(buttxt, f"userset {user_id} suniversal remname")
    if cfont != "Not Exists": buttons.sbutton("Delete CapFont", f"userset {user_id} cfont")
    buttons.sbutton("Close", f"userset {user_id} close")
    button = buttons.build_menu(2)

    text = f'''<u>Leech Settings for <a href='tg://user?id={user_id}'>{name}</a></u>

• Leech Type : <b>{ltype}</b>
• Custom Thumbnail : <b>{thumbmsg}</b>
• YT-DLP Quality is : <b><code>{escape(ytq)}</code></b>
• Prefix : <b>{escape(prefix)}</b>
• Suffix : <b>{suffix}</b>
• Caption : <b>{escape(caption)}</b>
• CapFont : {cfont}
• Remname : <b>{escape(remname)}</b>
• UserLog : <b>{userlog}</b>
• User Plan : <b>{uplan}</b>'''
    return text, button

def update_user_settings(message, from_user):
    msg, button = get_user_settings(from_user)
    editMessage(msg, message, button)

def user_settings(update, context):
    msg, button = get_user_settings(update.message.from_user)
    buttons_msg  = sendMarkup(msg, context.bot, update.message, button)

def set_yt_quality(update, context, omsg):
    message = update.message
    user_id = message.from_user.id
    handler_dict[user_id] = False
    value = message.text
    update_user_ldata(user_id, 'yt_ql', value)
    update.message.delete()
    update_user_settings(omsg, message.from_user)
    if DATABASE_URL:
        DbManger().update_user_data(user_id)

def set_addons(update, context, data, omsg):
    message = update.message
    user_id = message.from_user.id
    handler_dict[user_id] = False
    value = message.text
    update_user_ldata(user_id, data, value)
    update.message.delete()
    update_user_settings(omsg, message.from_user)
    if DATABASE_URL:
        DbManger().update_user_data(user_id)

def set_thumb(update, context, omsg):
    message = update.message
    user_id = message.from_user.id
    handler_dict[user_id] = False
    path = "Thumbnails/"
    if not ospath.isdir(path):
        mkdir(path)
    photo_dir = message.photo[-1].get_file().download()
    user_id = message.from_user.id
    des_dir = ospath.join(path, f'{user_id}.jpg')
    Image.open(photo_dir).convert("RGB").save(des_dir, "JPEG")
    osremove(photo_dir)
    update_user_ldata(user_id, 'thumb', des_dir)
    update.message.delete()
    update_user_settings(omsg, message.from_user)
    if DATABASE_URL:
        DbManger().update_thumb(user_id, des_dir)

def edit_user_settings(update, context):
    query = update.callback_query
    message = query.message
    user_id = query.from_user.id
    data = query.data
    data = data.split()
    if user_id != int(data[1]):
        query.answer(text="Not Yours!", show_alert=True)
    elif data[2] == "doc":
        update_user_ldata(user_id, 'as_doc', True)
        query.answer(text="Your File Will Deliver As Document!", show_alert=True)
        update_user_settings(message, query.from_user)
        if DATABASE_URL:
            DbManger().update_user_data(user_id)
    elif data[2] == "med":
        update_user_ldata(user_id, 'as_doc', False)
        query.answer(text="Your File Will Deliver As Media!", show_alert=True)
        update_user_settings(message, query.from_user)
        if DATABASE_URL:
            DbManger().update_user_data(user_id)
    elif data[2] == "dthumb":
        handler_dict[user_id] = False
        path = f"Thumbnails/{user_id}.jpg"
        if ospath.lexists(path):
            query.answer(text="Thumbnail Removed!", show_alert=True)
            osremove(path)
            update_user_ldata(user_id, 'thumb', '')
            update_user_settings(message, query.from_user)
            if DATABASE_URL:
                DbManger().update_thumb(user_id)
        else:
            query.answer(text="Old Settings", show_alert=True)
            update_user_settings(message, query.from_user)
    elif data[2] == "sthumb":
        query.answer()
        menu = False
        if handler_dict.get(user_id):
            handler_dict[user_id] = False
            sleep(0.5)
        start_time = time()
        handler_dict[user_id] = True
        buttons = ButtonMaker()
        thumbpath = f"Thumbnails/{user_id}.jpg"
        if ospath.exists(thumbpath):
            menu = True
            buttons.sbutton("Delete", f"userset {user_id} dthumb")
        buttons.sbutton("Back", f"userset {user_id} back")
        buttons.sbutton("Close", f"userset {user_id} close")
        editMessage('Send a photo to save it as custom Thumbnail.', message, buttons.build_menu(2) if menu else buttons.build_menu(1))
        partial_fnc = partial(set_thumb, omsg=message)
        photo_handler = MessageHandler(filters=Filters.photo & Filters.chat(message.chat.id) & Filters.user(user_id),
                                       callback=partial_fnc, run_async=True)
        dispatcher.add_handler(photo_handler)
        while handler_dict[user_id]:
            if time() - start_time > 60:
                handler_dict[user_id] = False
                update_user_settings(message, query.from_user)
        dispatcher.remove_handler(photo_handler)
    elif data[2] == 'ytq':
        query.answer()
        menu = False
        if handler_dict.get(user_id):
            handler_dict[user_id] = False
            sleep(0.5)
        start_time = time()
        handler_dict[user_id] = True
        buttons = ButtonMaker()
        if user_id in user_data and user_data[user_id].get('yt_ql'):
            menu = True
            buttons.sbutton("Delete", f"userset {user_id} rytq")
        buttons.sbutton("Back", f"userset {user_id} back")
        buttons.sbutton("Close", f"userset {user_id} close")
        rmsg = f'''
<u>Send YT-DLP Quality :</u>
Examples:
1. <code>{escape('bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]')}</code> this will give 1080p-mp4.
2. <code>{escape('bv*[height<=720][ext=webm]+ba/b[height<=720]')}</code> this will give 720p-webm.
Check all available qualities options <a href="https://github.com/yt-dlp/yt-dlp#filtering-formats">HERE</a>.
        '''
        editMessage(rmsg, message, buttons.build_menu(2) if menu else buttons.build_menu(1))
        partial_fnc = partial(set_yt_quality, omsg=message)
        value_handler = MessageHandler(filters=Filters.text & Filters.chat(message.chat.id) & Filters.user(user_id),
                                       callback=partial_fnc, run_async=True)
        dispatcher.add_handler(value_handler)
        while handler_dict[user_id]:
            if time() - start_time > 60:
                handler_dict[user_id] = False
                update_user_settings(message, query.from_user)
        dispatcher.remove_handler(value_handler)
    elif data[2] == 'rytq':
        query.answer(text="YT-DLP Quality Removed!", show_alert=True)
        update_user_ldata(user_id, 'yt_ql', '')
        update_user_settings(message, query.from_user)
        if DATABASE_URL:
            DbManger().update_user_data(user_id)
    elif data[2] == 'back':
        query.answer()
        handler_dict[user_id] = False
        update_user_settings(message, query.from_user)
    elif data[2] == "showthumb":
        path = f"Thumbnails/{user_id}.jpg"
        if ospath.lexists(path):
            msg = f"Thumbnail for: {query.from_user.mention_html()} (<code>{str(user_id)}</code>)"
            delo = sendPhoto(text=msg, bot=context.bot, message=message, photo=open(path, 'rb'))
            Thread(args=(context.bot, update.message, delo)).start()
        else: query.answer(text="Send new settings command.")
    elif data[2] == "suniversal":
        query.answer()
        menu = False
        if handler_dict.get(user_id):
            handler_dict[user_id] = False
            sleep(0.5)
        start_time = time()
        handler_dict[user_id] = True
        buttons = ButtonMaker()
        if data[3] == 'caption':
            buttons.sbutton("Set Font Style", f"userset {user_id} font")
        if user_id in user_data and user_data[user_id].get(data[3]):
            menu = True
            buttons.sbutton("Delete", f"userset {user_id} {data[3]}")
        buttons.sbutton("Back", f"userset {user_id} back")
        buttons.sbutton("Close", f"userset {user_id} close")
        editMessage(f'<u>Send {data[3].capitalize()} text :</u>\n\nExamples:\n1. Soon ... 😁', message, buttons.build_menu(2) if menu else buttons.build_menu(1))
        partial_fnc = partial(set_addons, data=data[3], omsg=message)
        UNI_HANDLER = f"{data[3]}_handler"
        UNI_HANDLER = MessageHandler(filters=Filters.text & Filters.chat(message.chat.id) & Filters.user(user_id),
                                       callback=partial_fnc, run_async=True)
        dispatcher.add_handler(UNI_HANDLER)
        while handler_dict[user_id]:
            if time() - start_time > 60:
                handler_dict[user_id] = False
                update_user_settings(message, query.from_user)
        dispatcher.remove_handler(UNI_HANDLER)
    elif data[2] == "prefix":
        handler_dict[user_id] = False
        update_user_ldata(user_id, 'prefix', False)
        if DATABASE_URL: 
            DbManger().update_userval(user_id, 'prefix')
        query.answer(text="Your Prefix is Successfully Deleted!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "suffix":
        handler_dict[user_id] = False
        update_user_ldata(user_id, 'suffix', False)
        if DATABASE_URL: 
            DbManger().update_userval(user_id, 'suffix')
        query.answer(text="Your Suffix is Successfully Deleted!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "caption":
        handler_dict[user_id] = False
        update_user_ldata(user_id, 'caption', False)
        if DATABASE_URL: 
            DbManger().update_userval(user_id, 'caption')
        query.answer(text="Your Caption is Successfully Deleted!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "remname":
        handler_dict[user_id] = False
        update_user_ldata(user_id, 'remname', False)
        if DATABASE_URL: 
            DbManger().update_userval(user_id, 'remname')
        query.answer(text="Your Remname is Successfully Deleted!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "userlog":
        handler_dict[user_id] = False
        update_user_ldata(user_id, 'userlog', False)
        if DATABASE_URL: 
            DbManger().update_userval(user_id, 'userlog')
        query.answer(text="Your UserLog is Successfully Deleted!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "cfont":
        handler_dict[user_id] = False
        update_user_ldata(user_id, 'cfont', False)
        if DATABASE_URL: 
            DbManger().update_userval(user_id, 'cfont')
        query.answer(text="Your Caption Font is Successfully Deleted!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "font":
        handler_dict[user_id] = False
        FONT_SPELL = {'b':'<b>Bold</b>', 'i':'<i>Italics</i>', 'code':'<code>Monospace</code>', 's':'<s>Strike</s>', 'u':'<u>Underline</u>', 'tg-spoiler':'<tg-spoiler>Spoiler</tg-spoiler>'}
        buttons = ButtonMaker()
        buttons.sbutton("Spoiler", f"userset {user_id} Spoiler")
        buttons.sbutton("Italics", f"userset {user_id} Italics")
        buttons.sbutton("Monospace", f"userset {user_id} Code")
        buttons.sbutton("Strike", f"userset {user_id} Strike")
        buttons.sbutton("Underline", f"userset {user_id} Underline")
        buttons.sbutton("Bold", f"userset {user_id} Bold")
        buttons.sbutton("Regular", f"userset {user_id} Regular")
        buttons.sbutton("Back", f"userset {user_id} back")
        buttons.sbutton("Close", f"userset {user_id} close")
        btns = buttons.build_menu(2)
        editMessage("<u>Change your Font Style from below:</u>\n\n• Current Style : " + user_data[user_id].get('cfont', [f'{FONT_SPELL[config_dict["CAPTION_FONT"]]} (Default)'])[0], message, btns)
    elif data[2] == "Spoiler":
        eVal = ["<tg-spoiler>Spoiler</tg-spoiler>", "tg-spoiler"]
        update_user_ldata(user_id, 'cfont', eVal)
        if DATABASE_URL:
            DbManger().update_userval(user_id, 'cfont', eVal)
            LOGGER.info(f"User : {user_id} Font Style Saved in DB")
        query.answer(text="Font Style changed to Spoiler!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "Italics":
        eVal = ["<i>Italics</i>", "i"]
        update_user_ldata(user_id, 'cfont', eVal)
        if DATABASE_URL:
            DbManger().update_userval(user_id, 'cfont', eVal)
            LOGGER.info(f"User : {user_id} Font Style Saved in DB")
        query.answer(text="Font Style changed to Italics!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "Code":
        eVal = ["<code>Monospace</code>", "code"]
        update_user_ldata(user_id, 'cfont', eVal)
        if DATABASE_URL:
            DbManger().update_userval(user_id, 'cfont', eVal)
            LOGGER.info(f"User : {user_id} Font Style Saved in DB")
        query.answer(text="Font Style changed to Monospace!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "Strike":
        eVal = ["<s>Strike</s>", "s"]
        update_user_ldata(user_id, 'cfont', eVal)
        if DATABASE_URL:
            DbManger().update_userval(user_id, 'cfont', eVal)
            LOGGER.info(f"User : {user_id} Font Style Saved in DB")
        query.answer(text="Font Style changed to Strike!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "Underline":
        eVal = ["<u>Underline</u>", "u"]
        update_user_ldata(user_id, 'cfont', eVal)
        if DATABASE_URL:
            DbManger().update_userval(user_id, 'cfont', eVal)
            LOGGER.info(f"User : {user_id} Font Style Saved in DB")
        query.answer(text="Font Style changed to Underline!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "Bold":
        eVal = ["<b>Bold</b>", "b"]
        update_user_ldata(user_id, 'cfont', eVal)
        if DATABASE_URL:
            DbManger().update_userval(user_id, 'cfont', eVal)
            LOGGER.info(f"User : {user_id} Font Style Saved in DB")
        query.answer(text="Font Style changed to Bold!", show_alert=True)
        update_user_settings(message, query.from_user)
    elif data[2] == "Regular":
        eVal = ["Regular", "r"]
        update_user_ldata(user_id, 'cfont', eVal)
        if DATABASE_URL:
            DbManger().update_userval(user_id, 'cfont', eVal)
            LOGGER.info(f"User : {user_id} Font Style Saved in DB")
        query.answer(text="Font Style changed to Regular!", show_alert=True)
        update_user_settings(message, query.from_user)
    else:
        query.answer()
        handler_dict[user_id] = False
        query.message.delete()
        query.message.reply_to_message.delete()

def send_users_settings(update, context):
    msg = ''.join(f'<code>{u}</code>: {escape(str(d))}\n\n' for u, d in user_data.items())
    if msg:
        sendMessage(msg, context.bot, update.message)
    else:
        sendMessage('No users data!', context.bot, update.message)

def sendPaidDetails(update, context):
    paid = ''
    for u, d in user_data.items():
        try:
            for ud, dd in d.items():
                if ud == 'is_paid' and dd is False:
                    paid += f"<code>{u}</code>\n"
        except: continue
    sendMessage(f'<b><u>Paid Users🤑 :</u></b>\n{paid}', context.bot, update.message)


pdetails_handler = CommandHandler(command=BotCommands.PaidUsersCommand, callback=sendPaidDetails,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
users_settings_handler = CommandHandler(BotCommands.UsersCommand, send_users_settings,
                                            filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
user_set_handler  = CommandHandler(BotCommands.UserSetCommand, user_settings,
                                   filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
but_set_handler = CallbackQueryHandler(edit_user_settings, pattern="userset", run_async=True)

dispatcher.add_handler(user_set_handler )
dispatcher.add_handler(but_set_handler)
dispatcher.add_handler(users_settings_handler)
dispatcher.add_handler(pdetails_handler)
