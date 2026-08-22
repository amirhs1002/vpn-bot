import json
import asyncio
import urllib3
import qrcode
import io
import random
import urllib.parse
import requests
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_BOT_TOKEN = "8769828959:AAGoyKmhtMZeFBUp2eLN-dOLWR-hjOHX5s"
OWNER_USERNAME = "amirhszz"
owner_chat_id = 6422509900

ADMINS_DATA = {
    "amirhszz": {"prefix": "Amir", "max_gb": None, "max_days": None, "prepaid_gb": 0.0},
    "goatserverss": {"prefix": "Goat", "max_gb": None, "max_days": None, "prepaid_gb": 0.0}
}

ADMINS_STATS = {}

PANEL_VOLUMETRIC_URL = "https://sw-r.arazcctv.ir:8000"
PANEL_VOLUMETRIC_USERNAME = "Goathszz"
PANEL_VOLUMETRIC_PASSWORD = "Goathszz"

PANEL_ECO_URL = "https://youpanel.temas-arvha.ir:2053"
PANEL_ECO_USERNAME = "rp6422509900_0b211fdd"
PANEL_ECO_PASSWORD = "LMQFmdeFAQ7EwvUr3h"

user_states = {}

def get_marzban_token(panel_url, username, password):
    url = f"{panel_url.rstrip('/')}/api/admin/token"
    payload = {"username": username, "password": password, "grant_type": "password"}
    try:
        response = requests.post(url, data=payload, verify=False, timeout=15)
        if response.status_code == 200:
            return response.json().get("access_token"), None
        else:
            return None, f"HTTP {response.status_code} - {response.text[:300]}"
    except Exception as e:
        return None, str(e)[:300]

def generate_qr_code(data: str) -> io.BytesIO:
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    bio.name = 'qrcode.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

def is_allowed_user(username: str) -> bool:
    if not username:
        return False
    return username.lower() in ADMINS_DATA

def is_owner(username: str) -> bool:
    if not username:
        return False
    return username.lower() == OWNER_USERNAME.lower()

def get_main_keyboard(username: str):
    keyboard = [
        [KeyboardButton("🚀 ساخت کانفینگ"), KeyboardButton("📦 ساخت کانفینگ عمده")],
        [KeyboardButton("📂 اشتراک‌های من")]
    ]
    if is_owner(username):
        keyboard.append([KeyboardButton("⚙️ مدیریت"), KeyboardButton("💾 بکاپ")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("❌ انصراف / لغو عملیات")]], resize_keyboard=True)

def get_panel_choice_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💎 پنل ویژه"), KeyboardButton("⚡ پنل اقتصادی")],
        [KeyboardButton("❌ انصراف / لغو عملیات")]
    ], resize_keyboard=True)

def get_sub_menu_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔍 دریافت مجدد اشتراک")],
        [KeyboardButton("❌ انصراف / لغو عملیات")]
    ], resize_keyboard=True)

def get_gb_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("5"), KeyboardButton("10"), KeyboardButton("20")],
        [KeyboardButton("❌ انصراف / لغو عملیات")]
    ], resize_keyboard=True)

def get_days_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("7"), KeyboardButton("30")],
        [KeyboardButton("❌ انصراف / لغو عملیات")]
    ], resize_keyboard=True)

def record_admin_stat(username: str, gb: float, count: int = 1):
    username = username.lower()
    if username not in ADMINS_STATS:
        ADMINS_STATS[username] = {"total_configs": 0, "total_gb": 0.0}
    ADMINS_STATS[username]["total_configs"] += count
    ADMINS_STATS[username]["total_gb"] += (gb * count)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in user_states:
        user_states.pop(user.id, None)

    if not is_allowed_user(user.username):
        await update.message.reply_text(
            f"✨ **سلام {user.first_name} عزیز، خوش آمدید!** ✨\n\n"
            "این ربات مخصوص مدیریت و ساخت کانفینگ اختصاصی ادمین‌هاست.\n"
            "💬 **@goatserverss**",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"🌟 **سلام {user.first_name} عزیز، خوش آمدید!** 🌟",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user.username)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMINS_DATA, ADMINS_STATS
    user = update.effective_user
    if not is_allowed_user(user.username):
        await update.message.reply_text(
            "🌸 کاربر گرامی، شما به بخش مدیریت دسترسی ندارید.\n💬 **@goatserverss**",
            parse_mode="Markdown"
        )
        return

    text = update.message.text.strip() if update.message and update.message.text else ""
    user_id = user.id

    if "انصراف" in text or "لغو" in text:
        if user_id in user_states:
            del user_states[user_id]
        await update.message.reply_text("🔙 عملیات لغو شد.", reply_markup=get_main_keyboard(user.username))
        return

    if text == "📂 اشتراک‌های من":
        user_states[user_id] = {"step": "choose_panel_subs"}
        await update.message.reply_text("⚙️ لطفاً پنل مورد نظر خود را برای مشاهده اشتراک‌ها انتخاب کنید:", reply_markup=get_panel_choice_keyboard())
        return

    if text == "🔍 دریافت مجدد اشتراک":
        if user_id in user_states and user_states[user_id].get("panel_type"):
            p_type = user_states[user_id]["panel_type"]
            user_states[user_id] = {"step": "get_existing_config_username", "panel_type": p_type}
            await update.message.reply_text(
                "👤 لطفاً **نام کاربری (Username)** کانفینگ مورد نظر خود را برای دریافت لینک وارد کنید:",
                parse_mode="Markdown",
                reply_markup=get_cancel_keyboard()
            )
        else:
            user_states[user_id] = {"step": "choose_panel_subs"}
            await update.message.reply_text("⚙️ لطفاً ابتدا پنل مورد نظر خود را انتخاب کنید:", reply_markup=get_panel_choice_keyboard())
        return

    if text == "⚙️ مدیریت" and is_owner(user.username):
        keyboard = [
            [InlineKeyboardButton("📊 گزارشات ادمین‌ها", callback_data="menu_reports")],
            [InlineKeyboardButton("⚙️ تنظیمات ادمین‌ها", callback_data="menu_manage_admins")],
            [InlineKeyboardButton("➕ افزودن ادمین جدید", callback_data="menu_add_admin")],
            [InlineKeyboardButton("🗑 حذف ادمین", callback_data="menu_remove_admin")]
        ]
        await update.message.reply_text("⚙️ **پنل مدیریت ربات:**\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if text == "💾 بکاپ" and is_owner(user.username):
        keyboard = [
            [InlineKeyboardButton("📥 دریافت فایل بکاپ", callback_data="backup_download")],
            [InlineKeyboardButton("📤 آپلود و بازگردانی بکاپ", callback_data="backup_upload")]
        ]
        await update.message.reply_text("💾 **بخش مدیریت پشتیبان (بکاپ):**\nمی‌توانید از اطلاعات ادمین‌ها و آمار بکاپ بگیرید یا آن را بازگردانی کنید:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if "ساخت کانفینگ عمده" in text:
        user_states[user_id] = {"step": "choose_panel_bulk"}
        await update.message.reply_text("⚙️ پنل مورد نظر را انتخاب کنید:", reply_markup=get_panel_choice_keyboard())
        return

    elif "ساخت کانفینگ" in text:
        user_states[user_id] = {"step": "choose_panel_single"}
        await update.message.reply_text("⚙️ پنل مورد نظر را انتخاب کنید:", reply_markup=get_panel_choice_keyboard())
        return

    if user_id in user_states:
        state_data = user_states[user_id]
        step = state_data.get("step")

        if step == "choose_panel_subs":
            if "پنل ویژه" in text:
                panel_type = "special"
            elif "پنل اقتصادی" in text:
                panel_type = "eco"
            else:
                await update.message.reply_text("❌ لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=get_panel_choice_keyboard())
                return

            user_states[user_id] = {"step": "view_subs_list", "panel_type": panel_type}
            admin_username = user.username.lower()
            admin_prefix = ADMINS_DATA.get(admin_username, {}).get("prefix", "")
            
            if not admin_prefix:
                await update.message.reply_text("❌ پیشوندی برای نام‌گذاری کانفینگ‌های شما یافت نشد.", reply_markup=get_main_keyboard(user.username))
                del user_states[user_id]
                return

            await update.message.reply_text("⏳ در حال دریافت لیست اشتراک‌ها از پنل انتخابی...")

            p_name = "💎 پنل ویژه" if panel_type == "special" else "⚡ پنل اقتصادی"
            p_url = PANEL_VOLUMETRIC_URL if panel_type == "special" else PANEL_ECO_URL
            p_user = PANEL_VOLUMETRIC_USERNAME if panel_type == "special" else PANEL_ECO_USERNAME
            p_pass = PANEL_VOLUMETRIC_PASSWORD if panel_type == "special" else PANEL_ECO_PASSWORD

            token, err = get_marzban_token(p_url, p_user, p_pass)
            active_configs = []
            expired_count = 0

            if token:
                try:
                    res = requests.get(
                        f"{p_url.rstrip('/')}/api/users",
                        headers={"Authorization": f"Bearer {token}"},
                        verify=False,
                        timeout=15
                    )
                    if res.status_code == 200:
                        data = res.json()
                        users_list = data.get("users", []) if isinstance(data, dict) else data
                        
                        for u in users_list:
                            u_name = u.get("username", "")
                            if u_name.startswith(admin_prefix + "_") or u_name == admin_prefix:
                                status = u.get("status", "")
                                expire_time = u.get("expire")
                                
                                is_expired = False
                                if status == "expired":
                                    is_expired = True
                                elif expire_time and expire_time < datetime.now().timestamp():
                                    is_expired = True

                                if is_expired:
                                    expired_count += 1
                                else:
                                    active_configs.append((p_name, u))
                except:
                    pass

            msg = f"📂 **وضعیت اشتراک‌های شما ({p_name}):**\n\n"
            msg += f"❌ **تعداد اشتراک‌های منقضی‌شده:** `{expired_count}` عدد\n"
            msg += f"✅ **تعداد اشتراک‌های فعال:** `{len(active_configs)}` عدد\n\n"

            if active_configs:
                msg += "📋 **لیست اشتراک‌های فعال:**\n"
                for idx, (_, conf) in enumerate(active_configs, 1):
                    c_username = conf.get("username")
                    c_used = conf.get("used_traffic", 0) / (1024 * 1024 * 1024)
                    c_limit = conf.get("data_limit", 0)
                    if c_limit:
                        c_limit = c_limit / (1024 * 1024 * 1024)
                        limit_str = f"{c_limit:.1f} GB"
                    else:
                        limit_str = "نامحدود"

                    msg += f"\n{idx}. `{c_username}`\n"
                    msg += f"   • مصرف: `{c_used:.2f} GB` از `{limit_str}`\n"
            else:
                msg += "📂 هیچ اشتراک فعالی با پیشوند شما در این پنل یافت نشد."

            if len(msg) > 4000:
                for x in range(0, len(msg), 4000):
                    await update.message.reply_text(msg[x:x+4000], parse_mode="Markdown")
                await update.message.reply_text("👇 برای دریافت مجدد لینک اشتراک روی دکمه زیر بزنید:", reply_markup=get_sub_menu_keyboard())
            else:
                await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_sub_menu_keyboard())
            return

        elif step == "get_existing_config_username":
            search_username = text.strip()
            admin_username = user.username.lower()
            admin_prefix = ADMINS_DATA.get(admin_username, {}).get("prefix", "")
            panel_type = state_data.get("panel_type", "special")

            if not is_owner(user.username):
                if not (search_username.startswith(admin_prefix + "_") or search_username == admin_prefix):
                    await update.message.reply_text(
                        f"❌ دسترسی غیرمجاز!\nشما فقط مجاز به دریافت کانفینگ‌های مربوط به پیشوند خودتان (`{admin_prefix}`) هستید.",
                        reply_markup=get_main_keyboard(user.username)
                    )
                    del user_states[user_id]
                    return

            del user_states[user_id]
            await update.message.reply_text("⏳ در حال جستجوی کانفینگ در پنل...")

            p_name = "💎 پنل ویژه" if panel_type == "special" else "⚡ پنل اقتصادی"
            p_url = PANEL_VOLUMETRIC_URL if panel_type == "special" else PANEL_ECO_URL
            p_user = PANEL_VOLUMETRIC_USERNAME if panel_type == "special" else PANEL_ECO_USERNAME
            p_pass = PANEL_VOLUMETRIC_PASSWORD if panel_type == "special" else PANEL_ECO_PASSWORD

            token, err = get_marzban_token(p_url, p_user, p_pass)
            found = False
            if token:
                try:
                    res = requests.get(
                        f"{p_url.rstrip('/')}/api/user/{search_username}",
                        headers={"Authorization": f"Bearer {token}"},
                        verify=False,
                        timeout=10
                    )
                    if res.status_code == 200:
                        found = True
                        u_data = res.json()
                        sub_path = u_data.get("subscription_url") or f"/sub/{u_data.get('uuid', '')}"
                        link = sub_path if sub_path.startswith("http") else f"{p_url.rstrip('/')}{sub_path}"

                        gb_limit = u_data.get("data_limit")
                        gb_val = f"{gb_limit / (1024**3):.1f} GB" if gb_limit else "نامحدود"
                        
                        expire_ts = u_data.get("expire")
                        exp_str = datetime.fromtimestamp(expire_ts).strftime('%Y-%m-%d') if expire_ts else "نامحدود"

                        qr_file = generate_qr_code(link)
                        caption_text = (
                            f"🔍 **اطلاعات کانفینگ ({p_name}):**\n\n"
                            f"👤 نام: `{search_username}`\n"
                            f"📊 حجم: `{gb_val}`\n"
                            f"⏳ انقضا: `{exp_str}`\n"
                            f"🔗 لینک اشتراک:\n`{link}`"
                        )

                        if "manual_cache" not in context.user_data:
                            context.user_data["manual_cache"] = {}
                        context.user_data["manual_cache"][search_username] = {
                            "target_url": p_url,
                            "token": token
                        }

                        inline_kb = InlineKeyboardMarkup([
                            [InlineKeyboardButton("📥 دریافت دستی سرور", callback_data=f"manual_{search_username}")]
                        ])

                        await update.message.reply_photo(
                            photo=qr_file,
                            caption=caption_text,
                            parse_mode="Markdown",
                            reply_markup=inline_kb
                        )
                except:
                    pass

            if not found:
                await update.message.reply_text("❌ کانفینگی با این نام کاربری در پنل مورد نظر پیدا نشد یا متعلق به شما نیست.", reply_markup=get_main_keyboard(user.username))
            else:
                await update.message.reply_text("✅ عملیات با موفقیت انجام شد.", reply_markup=get_main_keyboard(user.username))
            return

        elif step == "add_admin_username":
            new_admin = text.replace("@", "").strip().lower()
            state_data["new_admin"] = new_admin
            state_data["step"] = "add_admin_prefix"
            await update.message.reply_text("🏷 لطفاً نام پیش‌فرض را برای این ادمین وارد کنید:", reply_markup=get_cancel_keyboard())
            return

        elif step == "add_admin_prefix":
            prefix_name = text.replace(" ", "_").strip()
            new_admin = state_data["new_admin"]
            ADMINS_DATA[new_admin] = {"prefix": prefix_name, "max_gb": None, "max_days": None, "prepaid_gb": 0.0}
            del user_states[user_id]
            await update.message.reply_text(f"✅ ادمین `{new_admin}` اضافه شد!", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            return

        elif step == "remove_admin_username":
            target_admin = text.replace("@", "").strip().lower()
            if target_admin == OWNER_USERNAME.lower():
                await update.message.reply_text("❌ نمی‌توانید مالک اصلی را حذف کنید!", reply_markup=get_main_keyboard(user.username))
            elif target_admin in ADMINS_DATA:
                del ADMINS_DATA[target_admin]
                await update.message.reply_text(f"✅ ادمین `{target_admin}` حذف شد.", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            else:
                await update.message.reply_text("❌ یافت نشد.", reply_markup=get_main_keyboard(user.username))
            del user_states[user_id]
            return

        elif step == "set_max_gb":
            target = state_data["target_admin"]
            try:
                val = float(text) if text.lower() != "none" else None
                ADMINS_DATA[target]["max_gb"] = val
                del user_states[user_id]
                await update.message.reply_text(f"✅ محدودیت حجم ادمین `{target}` روی `{val} GB` تنظیم شد.", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            except ValueError:
                await update.message.reply_text("❌ عدد معتبر یا کلمه none را وارد کنید:")
            return

        elif step == "set_max_days":
            target = state_data["target_admin"]
            try:
                val = int(text) if text.lower() != "none" else None
                ADMINS_DATA[target]["max_days"] = val
                del user_states[user_id]
                await update.message.reply_text(f"✅ محدودیت روز ادمین `{target}` روی `{val} روز` تنظیم شد.", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            except ValueError:
                await update.message.reply_text("❌ عدد معتبر یا کلمه none را وارد کنید:")
            return

        elif step == "set_prepaid_gb":
            target = state_data["target_admin"]
            try:
                val = float(text)
                ADMINS_DATA[target]["prepaid_gb"] = val
                del user_states[user_id]
                await update.message.reply_text(f"✅ پیش‌خرید حجم ادمین `{target}` روی `{val} GB` تنظیم شد.", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            except ValueError:
                await update.message.reply_text("❌ عدد معتبر وارد کنید:")
            return

        elif step == "restore_backup":
            if update.message.document:
                try:
                    file = await update.message.document.get_file()
                    file_bytes = await file.download_as_bytearray()
                    backup_data = json.loads(file_bytes.decode("utf-8"))
                    
                    if "ADMINS_DATA" in backup_data:
                        ADMINS_DATA = backup_data["ADMINS_DATA"]
                    if "ADMINS_STATS" in backup_data:
                        ADMINS_STATS = backup_data["ADMINS_STATS"]

                    del user_states[user_id]
                    await update.message.reply_text("✅ اطلاعات و بکاپ با موفقیت بازگردانی شد!", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
                except Exception as e:
                    await update.message.reply_text(f"❌ خطا در خواندن فایل بکاپ:\n`{str(e)[:300]}`", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            else:
                await update.message.reply_text("❌ لطفاً فایل JSON پشتیبان را ارسال کنید:", reply_markup=get_cancel_keyboard())
            return

        elif step == "choose_panel_single":
            if "پنل ویژه" in text:
                state_data["panel_type"] = "special"
            elif "پنل اقتصادی" in text:
                state_data["panel_type"] = "eco"
            else:
                await update.message.reply_text("❌ لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=get_panel_choice_keyboard())
                return
            
            state_data["step"] = "single_get_gb"
            await update.message.reply_text("📊 حجم به گیگابایت را انتخاب کنید یا عدد دلخواه بفرستید:", reply_markup=get_gb_keyboard())
            return

        elif step == "choose_panel_bulk":
            if "پنل ویژه" in text:
                state_data["panel_type"] = "special"
            elif "پنل اقتصادی" in text:
                state_data["panel_type"] = "eco"
            else:
                await update.message.reply_text("❌ لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=get_panel_choice_keyboard())
                return
            state_data["step"] = "bulk_get_count"
            await update.message.reply_text("📦 تعداد کانفینگ‌ها را وارد کنید:", reply_markup=get_cancel_keyboard())
            return

        elif step == "single_get_gb":
            try:
                gb_size = float(text)
                admin_username = user.username.lower()
                admin_info = ADMINS_DATA.get(admin_username, {})
                
                prepaid = admin_info.get("prepaid_gb", 0.0)
                if prepaid > 0:
                    if gb_size <= prepaid:
                        ADMINS_DATA[admin_username]["prepaid_gb"] -= gb_size
                    else:
                        remaining_gb = gb_size - prepaid
                        ADMINS_DATA[admin_username]["prepaid_gb"] = 0.0
                        record_admin_stat(admin_username, remaining_gb, 1)
                        await update.message.reply_text(
                            f"⚠️ **اخطار محدودیت پیش‌خرید:**\nحجم پیش‌خرید شما تمام شد و `{remaining_gb} GB` مازاد بر روی فاکتور اصلی محاسبه گردید.",
                            parse_mode="Markdown"
                        )
                else:
                    if admin_info.get("max_gb") and gb_size > admin_info["max_gb"]:
                        await update.message.reply_text(f"❌ شما مجاز به ساخت کانفینگ با حجم بیشتر از `{admin_info['max_gb']} GB` نیستید!", parse_mode="Markdown")
                        return
                    record_admin_stat(admin_username, gb_size, 1)

                state_data["gb_size"] = gb_size
                state_data["step"] = "single_get_days"
                await update.message.reply_text("⏳ تعداد روز اعتبار را انتخاب کنید یا عدد دلخواه بفرستید:", reply_markup=get_days_keyboard())
            except ValueError:
                await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید:")
            return

        elif step == "single_get_days":
            try:
                expire_days = int(text)
                admin_info = ADMINS_DATA.get(user.username.lower(), {})
                if admin_info.get("max_days") and expire_days > admin_info["max_days"]:
                    await update.message.reply_text(f"❌ شما مجاز به ساخت کانفینگ با اعتبار بیشتر از `{admin_info['max_days']} روز` نیستید!", parse_mode="Markdown")
                    return
            except ValueError:
                await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید:")
                return

            panel_type = state_data["panel_type"]
            gb_size = state_data["gb_size"]
            
            admin_prefix = ADMINS_DATA.get(user.username.lower(), {}).get("prefix", "User")
            del user_states[user_id]

            await update.message.reply_text("⏳ در حال اتصال به پنل و ساخت کانفینگ...", reply_markup=get_main_keyboard(user.username))

            try:
                username_conf = f"{admin_prefix}_{int(datetime.now().timestamp())}"
                bytes_limit = int(gb_size * 1024 * 1024 * 1024) if gb_size > 0 else None
                expire_timestamp = int((datetime.now() + timedelta(days=expire_days)).timestamp()) if expire_days > 0 else None

                target_url = PANEL_VOLUMETRIC_URL if panel_type == "special" else PANEL_ECO_URL
                p_user = PANEL_VOLUMETRIC_USERNAME if panel_type == "special" else PANEL_ECO_USERNAME
                p_pass = PANEL_VOLUMETRIC_PASSWORD if panel_type == "special" else PANEL_ECO_PASSWORD

                token, err = get_marzban_token(target_url, p_user, p_pass)
                if not token:
                    await update.message.reply_text(f"❌ خطا در دریافت توکن پنل:\n`{err}`", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
                    return

                # تنظیم کلید groups متناسب با یوپنل (پنل اقتصادی) و مرزبان
                payload = {
                    "username": username_conf, 
                    "status": "active",
                    "data_limit": bytes_limit, 
                    "expire": expire_timestamp,
                    "proxies": {
                        "vless": {}, 
                        "trojan": {},
                        "vmess": {},
                        "shadowsocks": {}
                    },
                    "inbounds": {
                        "vless": [], 
                        "trojan": [],
                        "vmess": [],
                        "shadowsocks": []
                    },
                    "groups": ["all-migrated"]
                }
                if panel_type == "special":
                    payload["service"] = "Hajm"

                res = requests.post(
                    f"{target_url.rstrip('/')}/api/user",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    verify=False,
                    timeout=15
                )
                if res.status_code in [200, 201]:
                    data = res.json()
                    sub_path = data.get("subscription_url") or f"/sub/{data.get('uuid', '')}"
                    link = sub_path if sub_path.startswith("http") else f"{target_url.rstrip('/')}{sub_path}"

                    qr_file = generate_qr_code(link)
                    
                    caption_text = (
                        f"👤 نام: `{username_conf}`\n"
                        f"📊 حجم: `{gb_size} GB`\n"
                        f"⏳ اعتبار: `{expire_days} روز`\n"
                        f"🔗 لینک اشتراک:\n`{link}`"
                    )

                    if "manual_cache" not in context.user_data:
                        context.user_data["manual_cache"] = {}
                    
                    context.user_data["manual_cache"][username_conf] = {
                        "target_url": target_url,
                        "token": token
                    }

                    inline_kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📥 دریافت دستی سرور", callback_data=f"manual_{username_conf}")]
                    ])

                    await update.message.reply_photo(
                        photo=qr_file,
                        caption=caption_text,
                        parse_mode="Markdown",
                        reply_markup=inline_kb
                    )

                    if owner_chat_id and not is_owner(user.username):
                        try:
                            await context.bot.send_message(
                                chat_id=owner_chat_id,
                                text="🔔 **گزارش ثبت خرید جدید توسط ادمین:**\n\n"
                                     f"👨‍💻 ادمین: @{user.username}\n"
                                     f"⚙️ پنل: {'ویژه' if panel_type == 'special' else 'اقتصادی'}\n"
                                     f"👤 نام کاربری: `{username_conf}`\n"
                                     f"📊 حجم: `{gb_size} GB` | ⏳ روز: `{expire_days}`",
                                parse_mode="Markdown"
                            )
                        except:
                            pass
                else:
                    await update.message.reply_text(f"❌ خطای پاسخ پنل ({res.status_code}):\n`{res.text[:300]}`", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            except Exception as e:
                await update.message.reply_text(f"❌ خطای سیستمی رخ داد:\n`{str(e)[:300]}`", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            return

        elif step == "bulk_get_count":
            try:
                count = int(text)
                state_data["count"] = count
                state_data["step"] = "bulk_get_gb"
                await update.message.reply_text("📊 حجم هر کانفینگ را انتخاب کنید یا عدد دلخواه بفرستید:", reply_markup=get_gb_keyboard())
            except ValueError:
                await update.message.reply_text("❌ عدد معتبر وارد کنید:")
            return

        elif step == "bulk_get_gb":
            try:
                gb_size = float(text)
                admin_username = user.username.lower()
                admin_info = ADMINS_DATA.get(admin_username, {})
                count = state_data.get("count", 1)
                total_req_gb = gb_size * count

                prepaid = admin_info.get("prepaid_gb", 0.0)
                if prepaid > 0:
                    if total_req_gb <= prepaid:
                        ADMINS_DATA[admin_username]["prepaid_gb"] -= total_req_gb
                    else:
                        remaining_total = total_req_gb - prepaid
                        ADMINS_DATA[admin_username]["prepaid_gb"] = 0.0
                        record_admin_stat(admin_username, remaining_total, 1)
                        await update.message.reply_text(
                            f"⚠️ **اخطار محدودیت پیش‌خرید:**\nحجم پیش‌خرید شما تمام شد و مقدار مازاد روی فاکتور اصلی محاسبه گردید.",
                            parse_mode="Markdown"
                        )
                else:
                    if admin_info.get("max_gb") and gb_size > admin_info["max_gb"]:
                        await update.message.reply_text(f"❌ شما مجاز به ساخت کانفینگ با حجم بیشتر از `{admin_info['max_gb']} GB` نیستید!", parse_mode="Markdown")
                        return
                    record_admin_stat(admin_username, gb_size, count)

                state_data["gb_size"] = gb_size
                state_data["step"] = "bulk_get_days"
                await update.message.reply_text("⏳ تعداد روز اعتبار را انتخاب کنید یا عدد دلخواه بفرستید:", reply_markup=get_days_keyboard())
            except ValueError:
                await update.message.reply_text("❌ عدد معتبر وارد کنید:")
            return

        elif step == "bulk_get_days":
            try:
                expire_days = int(text)
                admin_info = ADMINS_DATA.get(user.username.lower(), {})
                if admin_info.get("max_days") and expire_days > admin_info["max_days"]:
                    await update.message.reply_text(f"❌ شما مجاز به ساخت کانفینگ با اعتبار بیشتر از `{admin_info['max_days']} روز` نیستید!", parse_mode="Markdown")
                    return
            except ValueError:
                await update.message.reply_text("❌ عدد معتبر وارد کنید:")
                return

            panel_type = state_data["panel_type"]
            count = state_data["count"]
            gb_size = state_data["gb_size"]
            
            admin_prefix = ADMINS_DATA.get(user.username.lower(), {}).get("prefix", "User")
            del user_states[user_id]

            await update.message.reply_text(f"⏳ در حال ساخت و ارسال {count} کانفینگ...", reply_markup=get_main_keyboard(user.username))

            try:
                target_url = PANEL_VOLUMETRIC_URL if panel_type == "special" else PANEL_ECO_URL
                token, err = get_marzban_token(target_url, PANEL_VOLUMETRIC_USERNAME if panel_type == "special" else PANEL_ECO_USERNAME, PANEL_VOLUMETRIC_PASSWORD if panel_type == "special" else PANEL_ECO_PASSWORD)

                if not token:
                    await update.message.reply_text(f"❌ خطا در اتصال به پنل: {err}", reply_markup=get_main_keyboard(user.username))
                    return

                success_count = 0
                failed = 0
                bytes_limit = int(gb_size * 1024 * 1024 * 1024) if gb_size > 0 else None
                expire_timestamp = int((datetime.now() + timedelta(days=expire_days)).timestamp()) if expire_days > 0 else None

                if "manual_cache" not in context.user_data:
                    context.user_data["manual_cache"] = {}

                for i in range(1, count + 1):
                    username_conf = f"{admin_prefix}_{i}_{int(datetime.now().timestamp())}"
                    
                    # تنظیم کلید groups متناسب با یوپنل (پنل اقتصادی) و مرزبان
                    payload = {
                        "username": username_conf, 
                        "status": "active",
                        "data_limit": bytes_limit, 
                        "expire": expire_timestamp,
                        "proxies": {
                            "vless": {}, 
                            "trojan": {},
                            "vmess": {},
                            "shadowsocks": {}
                        },
                        "inbounds": {
                            "vless": [], 
                            "trojan": [],
                            "vmess": [],
                            "shadowsocks": []
                        },
                        "groups": ["all-migrated"]
                    }
                    if panel_type == "special":
                        payload["service"] = "Hajm"

                    try:
                        res = requests.post(
                            f"{target_url.rstrip('/')}/api/user", 
                            json=payload, 
                            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, 
                            verify=False,
                            timeout=10
                        )
                        if res.status_code in [200, 201]:
                            success_count += 1
                            data = res.json()
                            sub_path = data.get("subscription_url") or f"/sub/{data.get('uuid', '')}"
                            link = sub_path if sub_path.startswith("http") else f"{target_url.rstrip('/')}{sub_path}"

                            qr_file = generate_qr_code(link)
                            caption_text = (
                                f"📦 **کانفینگ شماره {i} از {count}**\n\n"
                                f"👤 نام: `{username_conf}`\n"
                                f"📊 حجم: `{gb_size} GB`\n"
                                f"⏳ اعتبار: `{expire_days} روز`\n"
                                f"🔗 لینک اشتراک:\n`{link}`"
                            )
                            
                            context.user_data["manual_cache"][username_conf] = {
                                "target_url": target_url,
                                "token": token
                            }

                            inline_kb = InlineKeyboardMarkup([
                                [InlineKeyboardButton("📥 دریافت دستی سرور", callback_data=f"manual_{username_conf}")]
                            ])
                            
                            await update.message.reply_photo(photo=qr_file, caption=caption_text, parse_mode="Markdown", reply_markup=inline_kb)
                        else:
                            failed += 1
                    except:
                        failed += 1

                await update.message.reply_text(f"📦 **گزارش نهایی ساخت عمده:**\n✅ موفق و ارسال‌شده: {success_count}\n❌ ناموفق: {failed}", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))

                if owner_chat_id and not is_owner(user.username):
                    try:
                        await context.bot.send_message(
                            chat_id=owner_chat_id,
                            text="📦 **گزارش ساخت عمده توسط ادمین:**\n\n" +
                                 f"👨‍💻 ادمین: @{user.username}\n" +
                                 f"⚙️ پنل: {'ویژه' if panel_type == 'special' else 'اقتصادی'}\n" +
                                 f"✅ تعداد موفق: {success_count}\n" +
                                 f"❌ ناموفق: {failed}",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
            except Exception as e:
                await update.message.reply_text(f"❌ خطای سیستمی در ساخت عمده:\n`{str(e)[:300]}`", parse_mode="Markdown", reply_markup=get_main_keyboard(user.username))
            return

    else:
        await update.message.reply_text("❓ لطفاً از منوی زیر انتخاب کنید:", reply_markup=get_main_keyboard(user.username))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("manual_"):
        await query.answer("⏳ در حال استخراج و ساخت سرورهای رندوم...", show_alert=False)
        username_conf = data.replace("manual_", "", 1)

        manual_cache = context.user_data.get("manual_cache", {})
        conf_info = manual_cache.get(username_conf)

        if not conf_info:
            await query.message.reply_text("❌ اطلاعات این کانفینگ منقضی شده است. لطفاً دوباره کانفینگ بسازید.")
            return

        target_url = conf_info["target_url"]
        token = conf_info["token"]

        try:
            res = requests.get(
                f"{target_url.rstrip('/')}/api/user/{username_conf}",
                headers={"Authorization": f"Bearer {token}"},
                verify=False,
                timeout=10
            )
            if res.status_code == 200:
                user_data = res.json()
                links = user_data.get("links", [])
                
                if not links:
                    proxies = user_data.get("proxies", {})
                    for p_type, p_val in proxies.items():
                        if isinstance(p_val, dict) and "links" in p_val:
                            links.extend(p_val["links"])

                if not links:
                    sub_url = user_data.get("subscription_url")
                    if sub_url:
                        links = [sub_url if sub_url.startswith("http") else f"{target_url.rstrip('/')}{sub_url}"]

                if links:
                    selected_links = random.sample(links, min(5, len(links)))
                    
                    await query.message.reply_text(f"🔍 **۵ لوکیشن و سرور رندوم برای `{username_conf}`:**", parse_mode="Markdown")
                    
                    for idx, link in enumerate(selected_links, 1):
                        config_name = "سرور ناشناس"
                        if "#" in link:
                            raw_name = link.split("#")[-1]
                            config_name = urllib.parse.unquote(raw_name)

                        qr_bio = generate_qr_code(link)
                        await query.message.reply_photo(
                            photo=qr_bio,
                            caption=f"📍 **{config_name}**\n\n`{link}`",
                            parse_mode="Markdown"
                        )
                else:
                    await query.message.reply_text("❌ هیچ لینک سرور مجزایی برای این کانفینگ یافت نشد.")
            else:
                await query.message.reply_text("❌ خطا در برقراری ارتباط با پنل جهت دریافت لینک‌ها.")
        except Exception as e:
            await query.message.reply_text(f"❌ خطا: {str(e)[:200]}")
        return

    await query.answer()

    if data == "menu_reports":
        keyboard = []
        for adm in ADMINS_DATA.keys():
            keyboard.append([InlineKeyboardButton(f"👤 @{adm}", callback_data=f"report_{adm}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی مدیریت", callback_data="menu_back_main")])
        await query.edit_message_text("📊 **لیست ادمین‌ها جهت مشاهده گزارشات خرید:**\nروی نام ادمین مورد نظر کلیک کنید:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_manage_admins":
        keyboard = []
        for adm in ADMINS_DATA.keys():
            keyboard.append([InlineKeyboardButton(f"⚙️ تنظیمات @{adm}", callback_data=f"manage_{adm}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی مدیریت", callback_data="menu_back_main")])
        await query.edit_message_text("⚙️ **مدیریت ادمین‌ها:**\nبرای اعمال محدودیت حجم/روز یا پیش‌خرید روی ادمین مورد نظر کلیک کنید:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "menu_add_admin":
        user_states[query.from_user.id] = {"step": "add_admin_username"}
        await query.edit_message_text("👤 لطفاً یوزرنیم تلگرام ادمین جدید را بدون علامت @ وارد کنید:\n*(برای لغو به منوی اصلی برگردید)*", parse_mode="Markdown")

    elif data == "menu_remove_admin":
        user_states[query.from_user.id] = {"step": "remove_admin_username"}
        admins_list = "\n".join([f"• `{adm}`" for adm in ADMINS_DATA.keys() if adm.lower() != OWNER_USERNAME.lower()])
        if not admins_list:
            admins_list = "هیچ ادمین دیگری وجود ندارد."
        await query.edit_message_text(f"🗑 ادمین‌های فعلی:\n{admins_list}\n\n👤 یوزرنیم ادمینی که می‌خواهید حذف کنید را وارد کنید:", parse_mode="Markdown")

    elif data == "menu_back_main":
        keyboard = [
            [InlineKeyboardButton("📊 گزارشات ادمین‌ها", callback_data="menu_reports")],
            [InlineKeyboardButton("⚙️ تنظیمات ادمین‌ها", callback_data="menu_manage_admins")],
            [InlineKeyboardButton("➕ افزودن ادمین جدید", callback_data="menu_add_admin")],
            [InlineKeyboardButton("🗑 حذف ادمین", callback_data="menu_remove_admin")]
        ]
        await query.edit_message_text("⚙️ **پنل مدیریت ربات:**\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "backup_download":
        backup_dict = {
            "ADMINS_DATA": ADMINS_DATA,
            "ADMINS_STATS": ADMINS_STATS
        }
        json_bytes = io.BytesIO(json.dumps(backup_dict, ensure_ascii=False, indent=4).encode("utf-8"))
        json_bytes.name = f"bot_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        await query.message.reply_document(
            document=json_bytes,
            caption="💾 **فایل پشتیبان (بکاپ) اطلاعات ادمین‌ها و آمار:**",
            parse_mode="Markdown"
        )

    elif data == "backup_upload":
        user_states[query.from_user.id] = {"step": "restore_backup"}
        await query.edit_message_text("📤 لطفاً فایل JSON پشتیبان (بکاپ) خود را ارسال کنید تا اطلاعات بازگردانی شود:", parse_mode="Markdown")

    elif data.startswith("report_"):
        adm = data.split("_")[1]
        stat = ADMINS_STATS.get(adm.lower(), {"total_configs": 0, "total_gb": 0.0})
        prepaid_val = ADMINS_DATA.get(adm.lower(), {}).get("prepaid_gb", 0.0)
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_reports")]]
        await query.edit_message_text(
            f"📊 **گزارش خرید ادمین @{adm}:**\n\n"
            f"📦 تعداد کل خریدها: `{stat['total_configs']}` عدد\n"
            f"📊 مجموع حجم فاکتور اصلی: `{stat['total_gb']} GB`\n"
            f"⚡ حجم پیش‌خرید باقی‌مانده: `{prepaid_val} GB`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("manage_"):
        adm = data.split("_")[1]
        admin_info = ADMINS_DATA.get(adm.lower(), {})
        max_gb = admin_info.get("max_gb", "نامحدود")
        max_days = admin_info.get("max_days", "نامحدود")
        prepaid_gb = admin_info.get("prepaid_gb", 0.0)

        keyboard = [
            [InlineKeyboardButton("💳 تسویه حساب (صفر کردن آمار)", callback_data=f"clear_{adm}")],
            [InlineKeyboardButton("📊 تغییر محدودیت حجم", callback_data=f"limitgb_{adm}")],
            [InlineKeyboardButton("⏳ تغییر محدودیت روز", callback_data=f"limitdays_{adm}")],
            [InlineKeyboardButton("⚡ تنظیم پیش‌خرید حجم", callback_data=f"prepaid_{adm}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_manage_admins")]
        ]
        await query.edit_message_text(
            f"⚙️ **تنظیمات ادمین @{adm}:**\n\n"
            f"• سقف حجم مجاز: `{max_gb}`\n"
            f"• سقف روز مجاز: `{max_days}`\n"
            f"• حجم پیش‌خرید شده: `{prepaid_gb} GB`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("clear_"):
        adm = data.split("_")[1].lower()
        if adm in ADMINS_STATS:
            ADMINS_STATS[adm] = {"total_configs": 0, "total_gb": 0.0}
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به تنظیمات ادمین", callback_data=f"manage_{adm}")]]
        await query.edit_message_text(f"✅ حساب ادمین `{adm}` تسویه و آمار خریدها صفر شد.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("limitgb_"):
        adm = data.split("_")[1].lower()
        user_states[query.from_user.id] = {"step": "set_max_gb", "target_admin": adm}
        await query.edit_message_text(f"📊 لطفاً سقف حجم مجاز برای ادمین `@{adm}` را به گیگابایت وارد کنید (برای نامحدود کلمه `none` را بفرستید):", parse_mode="Markdown")

    elif data.startswith("limitdays_"):
        adm = data.split("_")[1].lower()
        user_states[query.from_user.id] = {"step": "set_max_days", "target_admin": adm}
        await query.edit_message_text(f"⏳ لطفاً سقف روز اعتبار برای ادمین `@{adm}` را وارد کنید (برای نامحدود کلمه `none` را بفرستید):", parse_mode="Markdown")

    elif data.startswith("prepaid_"):
        adm = data.split("_")[1].lower()
        user_states[query.from_user.id] = {"step": "set_prepaid_gb", "target_admin": adm}
        await query.edit_message_text(f"⚡ لطفاً مقدار حجم پیش‌خرید جدید برای ادمین `@{adm}` را به گیگابایت وارد کنید:", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
