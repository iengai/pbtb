from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)
from .config import BOT_TOKEN, ALLOWED_USER_IDS
from .db import list_all_bots, list_all_enabled_bots
from .process import start_bot, stop_bot, get_bot_pid_if_running, add_bot
from .pb_config import list_predefined, apply_pb_config
import re

# 对话状态常量
ADD_BOT_ID, ADD_BOT_KEY, ADD_BOT_SECRET = range(3)

# 回调数据类型
SHOW_BOT_LIST = "show_bot_list"
SELECT_BOT = "select_bot::"
BACK_TO_PANEL = "back_to_panel"

user_add_context = {}


# ===================== 权限控制装饰器 =====================
def restricted(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id not in ALLOWED_USER_IDS:
            if update.message:
                await update.message.reply_text("⛔️ 你没有权限控制这个 bot。")
            elif update.callback_query:
                await update.callback_query.answer("⛔️ 无操作权限")
            return
        return await func(update, context)

    return wrapper


# ===================== 面板核心逻辑 =====================
async def generate_panel_buttons():
    """生成主面板按钮布局"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 机器人列表", callback_data=SHOW_BOT_LIST),
         InlineKeyboardButton("📊 当前状态", callback_data="refresh")],
        [InlineKeyboardButton("🔁 重启运行", callback_data="restart"),
         InlineKeyboardButton("🛑 停止运行", callback_data="stop")],
        [InlineKeyboardButton("🧩 配置模板", callback_data="configure"),
         InlineKeyboardButton("➕ 添加Bot", callback_data="addbot")]
    ])


async def show_panel(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """通过回调更新面板"""
    bots = list_all_bots(query.from_user.id)
    selected = context.user_data.get("selected_bot")

    if selected not in bots:
        selected = None

    status_msg = "🎛 当前选中 bot: 无\n状态: ⚠️ 未选中任何 bot\n" if not selected else \
        f"🎛 当前选中 bot: `{selected}`\n状态: {'🟢 运行中' if get_bot_pid_if_running(selected) else '🔴 已停止'}\n"

    await query.edit_message_text(
        text=status_msg,
        parse_mode="Markdown",
        reply_markup=await generate_panel_buttons()
    )


async def show_panel_via_message(message: Message):
    """通过消息命令展示面板"""
    await message.reply_text(
        text="🤖 机器人控制中心",
        parse_mode="Markdown",
        reply_markup=await generate_panel_buttons()
    )


@restricted
async def panel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """面板命令入口"""
    if update.message:
        await show_panel_via_message(update.message)
    elif update.callback_query:
        await show_panel(update.callback_query, context)


# ===================== 机器人列表功能 =====================
async def show_bot_list(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """显示可选机器人列表"""
    bots = [x[0] for x in list_all_bots(query.from_user.id)]

    if not bots:
        await query.edit_message_text("📭 当前没有可用机器人")
        return

    # 生成机器人按钮（每行2个）
    bot_buttons = []
    row = []

    for idx, (bot_id) in enumerate(bots):
        btn = InlineKeyboardButton(
            text=f"{'⭐' if context.user_data.get('selected_bot') == bot_id else '○'} {bot_id}",
            callback_data=f"{SELECT_BOT}{bot_id}"
        )
        row.append(btn)
        if (idx + 1) % 2 == 0:
            bot_buttons.append(row)
            row = []

    if row:  # 处理剩余按钮
        bot_buttons.append(row)

    # 添加返回按钮
    bot_buttons.append([InlineKeyboardButton("🔙 返回主面板", callback_data=BACK_TO_PANEL)])

    await query.edit_message_text(
        text="📜 可用机器人列表：",
        reply_markup=InlineKeyboardMarkup(bot_buttons)
    )


# ===================== 按钮回调处理 =====================
@restricted
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    bots = [x[0] for x in list_all_bots(query.from_user.id)]
    selected = context.user_data.get("selected_bot")
    if len(bots) == 0:
        selected = None
    elif selected is None:
        selected = bots[0][0]

    # 处理机器人列表
    if data == SHOW_BOT_LIST:
        await show_bot_list(query, context)
        return

        # 处理机器人选择
    if data.startswith(SELECT_BOT):

        bot_id = data[len(SELECT_BOT):]
        print(bot_id)
        print(bots)
        if bot_id not in bots:
            raise Exception("invalid bot_id")
        context.user_data["selected_bot"] = bot_id
        await query.edit_message_text(
            f"✅ 已选择机器人：`{bot_id}`\n"
            f"使用 /panel 返回控制面板",
            parse_mode="Markdown"
        )
        return

    # 处理返回面板
    if data == BACK_TO_PANEL:
        await show_panel(query,context)
        return

    # 处理模板配置
    if data.startswith("template::"):
        try:
            bot_id = selected
            template_name = data.split("::")[1]
            if not bot_id:
                raise ValueError("请先选择要配置的Bot")

            apply_pb_config(bot_id, template_name)
            await query.edit_message_text(
                f"⚙️ 已为 `{bot_id}` 应用模板\n• 配置已更新\n• 需自动重启",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.edit_message_text(f"❌ 操作失败：{str(e)}")
        return

    # 处理其他控制命令

    # 处理模板配置入口
    if data == "configure":
        if not selected:
            await query.edit_message_text("❗️请先在列表中选择Bot")
            return

        templates = list_predefined()
        if not templates:
            await query.edit_message_text("⚠️ 当前没有可用模板")
            return

        template_buttons = [
            [InlineKeyboardButton(f"📜 {name}", callback_data=f"template::{name}")]
            for idx, name in enumerate(templates)
        ]
        template_buttons.append([InlineKeyboardButton("🔙 返回", callback_data=BACK_TO_PANEL)])

        await query.edit_message_text(
            f"🛠 为 `{selected}` 选择模板：",
            reply_markup=InlineKeyboardMarkup(template_buttons),
            parse_mode="Markdown"
        )
        return
    # 处理模板应用
    if data.startswith("template::"):
        try:
            if selected is None:
                raise ValueError("请先在主面板选择Bot")

            template_idx = int(data.split("::")[1])
            apply_pb_config(selected, template_idx)
            await query.edit_message_text(
                f"⚙️ 配置更新成功！\n"
                f"• 机器人: `{selected}`\n"
                f"• 已应用新模板\n"
                f"• 服务已自动重启",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.edit_message_text(f"❌ 操作失败：{str(e)}")
        return

    if data in ["refresh", "restart", "stop"]:
        if not selected:
            await query.edit_message_text("❗️请先选择Bot")
            return

        if data == "refresh":
            status = "🟢 运行中" if get_bot_pid_if_running(selected) else "🔴 已停止"
            await query.edit_message_text(f"📊 {selected} 状态：{status}")
        elif data == "restart":
            stop_bot(selected)
            start_bot(selected)
            await query.edit_message_text(f"🔄 已重启 {selected}")
        elif data == "stop":
            stop_bot(selected)
            await query.edit_message_text(f"⏹️ 已停止 {selected}")


# ===================== 添加Bot流程 =====================
@restricted
async def add_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🆕 请输入新Bot的ID（字母数字组合，不带空格）：\n"
        "输入 /cancel 取消操作"
    )
    return ADD_BOT_ID


@restricted
async def add_bot_id_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_id = update.message.text.strip()

    if not bot_id.isalnum():
        await update.message.reply_text("❌ ID只能包含字母和数字，请重新输入：")
        return ADD_BOT_ID

    user_add_context[user_id] = {"bot_id": bot_id}
    await update.message.reply_text("🔑 请输入API Key：")
    return ADD_BOT_KEY


@restricted
async def add_bot_key_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_add_context[user_id]["key"] = update.message.text.strip()
    await update.message.reply_text("🔐 请输入API Secret：")
    return ADD_BOT_SECRET


@restricted
async def add_bot_secret_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = user_add_context.pop(user_id)

    try:
        add_bot(
            user_data["bot_id"],
            update.effective_user.id,
            user_data["key"],
            update.message.text.strip()
        )
        await update.message.reply_text(
            f"✅ Bot `{user_data['bot_id']}` 添加成功！",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ 添加失败：{str(e)}")

    return ConversationHandler.END


# ===================== 其他功能 =====================
@restricted
async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.clear()
    user_add_context.pop(user_id, None)
    await update.message.reply_text("❌ 操作已取消")
    return ConversationHandler.END


@restricted
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 欢迎使用机器人管理器\n\n"
        "使用 /panel 进入控制面板\n"
        "输入 /help 查看详细帮助"
    )


@restricted
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📘 帮助手册\n\n"
        "▫️ /panel - 主控制面板\n"
        "▫️ /list - 查看机器人列表\n"
        "▫️ /cancel - 取消当前操作\n"
        "▫️ /help - 显示本帮助\n\n"
        "🛠 控制面板功能：\n"
        "- 查看/选择机器人\n"
        "- 实时状态监控\n"
        "- 重启/停止机器人\n"
        "- 应用配置模板\n"
        "- 添加新机器人"
    )
    await update.message.reply_text(help_text)


def init_bots():
    for enabled_bot in list_all_enabled_bots():
        start_bot(enabled_bot[0])

# ===================== 应用启动 =====================
def start_telegram_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 添加Bot对话处理器
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_bot_start, pattern="^addbot$")],
        states={
            ADD_BOT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bot_id_step)],
            ADD_BOT_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bot_key_step)],
            ADD_BOT_SECRET: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bot_secret_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel_cmd)],
    ))

    # 注册回调处理器
    app.add_handler(CallbackQueryHandler(
        button_handler,
        pattern=re.compile(r"^(?!addbot$).*")
    ))

    # 注册命令
    commands = [
        ("start", start_cmd),
        ("help", help_cmd),
        ("panel", panel_cmd),
        ("cancel", cancel_cmd)
    ]
    for cmd, handler in commands:
        app.add_handler(CommandHandler(cmd, handler))

    print("✅ 机器人管理器已启动")
    app.run_polling()