# bot/handlers/groups.py - FULLY IMPLEMENTED
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
import requests
from ..locales import t

API_BASE_URL = "http://127.0.0.1:8000"

# States
(
    GROUP_MENU,
    GROUP_CREATE_NAME,
    GROUP_CREATE_DESC,
    GROUP_VIEW,
    ADD_MEMBER_USERNAME,
    REMOVE_MEMBER_SELECT,
) = range(20, 26)


async def get_groups_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, as_new_message=False):
    """Fetches user's groups and displays them as a menu."""
    lang = context.user_data.get("lang", "en")
    user_id = context.user_data.get("system_user_id")
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/groups")
        response.raise_for_status()
        groups = response.json()
        keyboard = [
            [InlineKeyboardButton(g["name"], callback_data=f"group_view_{g['id']}")]
            for g in groups
        ]
        keyboard.append(
            [InlineKeyboardButton(t("btn_create_group", lang), callback_data="group_create_new")]
        )
        message_text = t("groups_select_prompt", lang)
        
        if as_new_message or not update.callback_query:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                message_text, reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Error: {e}"
        )
    return GROUP_MENU


async def my_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("is_logged_in"):
        await update.message.reply_text("Please /login first.")
        return ConversationHandler.END
    return await get_groups_menu(update, context, as_new_message=True)


async def group_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")

    if query.data == "group_create_new":
        await query.edit_message_text(t("create_group_ask_name", lang))
        return GROUP_CREATE_NAME
    else:  # View a group
        group_id = int(query.data.split("_")[2])
        context.user_data["current_group_id"] = group_id
        
        response = requests.get(f"{API_BASE_URL}/users/{context.user_data['system_user_id']}/groups")
        group = next((g for g in response.json() if g["id"] == group_id), None)
        context.user_data["current_group_members"] = group["members"]
        context.user_data["current_group_name"] = group["name"]
        
        header = t("group_details_header", lang, group_name=group["name"])
        members_text = t("group_members_title", lang) + "\n- " + "\n- ".join([m["name"] for m in group["members"]])
        
        keyboard = [
            [InlineKeyboardButton(t("btn_add_member", lang), callback_data="group_action_add")],
            [InlineKeyboardButton(t("btn_remove_member", lang), callback_data="group_action_remove")],
            [InlineKeyboardButton(t("btn_back_to_groups", lang), callback_data="group_action_back")],
        ]
        await query.edit_message_text(f"{header}\n\n{members_text}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return GROUP_VIEW


async def group_view_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    
    if query.data == "group_action_add":
        await query.edit_message_text(t("ask_add_member_name", lang))
        return ADD_MEMBER_USERNAME
    elif query.data == "group_action_remove":
        members = context.user_data["current_group_members"]
        user_id = context.user_data["system_user_id"]
        keyboard = [[InlineKeyboardButton(m['name'], callback_data=f"remove_user_{m['id']}")] for m in members if m['id'] != user_id]
        if not keyboard:
             await context.bot.send_message(chat_id=update.effective_chat.id, text="No other members to remove.")
             return GROUP_VIEW
        await query.edit_message_text(t("ask_remove_member", lang), reply_markup=InlineKeyboardMarkup(keyboard))
        return REMOVE_MEMBER_SELECT
    elif query.data == "group_action_back":
        return await get_groups_menu(update, context)


async def received_add_member_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username_to_add = update.message.text
    group_id = context.user_data['current_group_id']
    lang = context.user_data.get('lang', 'en')
    try:
        user_res = requests.get(f"{API_BASE_URL}/users/by-name/{username_to_add}")
        if user_res.status_code != 200:
            await update.message.reply_text(t("user_not_found", lang, username=username_to_add))
            return await get_groups_menu(update, context, as_new_message=True)
        
        user_id_to_add = user_res.json()['id']
        add_res = requests.post(f"{API_BASE_URL}/groups/{group_id}/add_member/{user_id_to_add}")
        if add_res.status_code == 200:
            await update.message.reply_text(t("add_member_success", lang, username=username_to_add))
        else:
            await update.message.reply_text(f"Error: {add_res.json().get('detail')}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    return await get_groups_menu(update, context, as_new_message=True)

async def received_remove_member_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id_to_remove = int(query.data.split('_')[2])
    group_id = context.user_data['current_group_id']
    lang = context.user_data.get('lang', 'en')
    
    try:
        # Before calling remove, get the user's name for the success message
        members = context.user_data['current_group_members']
        user_to_remove = next((m for m in members if m['id'] == user_id_to_remove), None)
        username_to_remove = user_to_remove['name'] if user_to_remove else "member"

        res = requests.delete(f"{API_BASE_URL}/groups/{group_id}/remove_member/{user_id_to_remove}")
        if res.status_code == 200:
            await query.edit_message_text(t("remove_member_success", lang, username=username_to_remove))
        else:
            await query.edit_message_text(f"Error: {res.json().get('detail')}")
    except Exception as e:
        await query.edit_message_text(f"Error: {e}")
    return await get_groups_menu(update, context, as_new_message=False)


async def received_group_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_group_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(t("create_group_ask_desc", lang, group_name=update.message.text))
    return GROUP_CREATE_DESC

async def received_group_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    group_name = context.user_data['new_group_name']
    lang = context.user_data.get('lang', 'en')
    
    payload = {"name": group_name, "description": description}
    response = requests.post(f"{API_BASE_URL}/groups", json=payload)
    
    if response.status_code == 201:
        await update.message.reply_text(t("group_created_success", lang, group_name=group_name))
    else:
        await update.message.reply_text(f"Error: {response.json().get('detail')}")
        
    del context.user_data['new_group_name']
    return await get_groups_menu(update, context, as_new_message=True)