import logging
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    PicklePersistence,
    Defaults
)
from telegram.constants import ParseMode
import random

# ==========================================
# KONFIGURASI DAN GLOBAL DEFAULTS
# ==========================================
TOKEN = "8747562941:AAEGyf4mO-6bsEYcBbqfA0Apv96eDwTkc_M"
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=JAKARTA_TZ)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

SPAM_MESSAGES = [
    "BANGUN MEOW! Tugas {nama} MASIH NUGU! 😾🔥",
    "Kamu mau F di mata guru? KERJAIN SEKARANG! 😾",
    "Mager? Deadline ga mager meow! 🐾",
    "Tugas {nama} nunggu kamu loh meow 😿😭",
    "MEOW UDAH PERINGATKAN! MASIH BELUM JUGA? 🤬",
    "NILAI kamu mau amblas gara2 {nama}? KERJA! 📉➡️📈",
    "WAKTU KAMU HABIS! TUGAS {nama} UDAH MEPET! ⏰💥",
    "Kamu kira meow bercanda? SPAM MODE ON! 😼⚡",
    "Tugas {nama} = Masa depan kamu. Kerjain! 🌟",
    "STOP SCROLLING! KERJAIN TUGAS MEOW! 📱➡️📚"
]

def get_progress_bar(percent):
    """Menghasilkan bar visual loading menggunakan Unicode blok"""
    length = 10
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percent}%"

def parse_target_datetime(date_str, time_str):
    """Mengonversi input DD-MM dan HH:MM ke objek datetime aware"""
    try:
        now = datetime.now(JAKARTA_TZ)
        day, month = map(int, date_str.split('-'))
        hour, minute = map(int, time_str.split(':'))
        
        target = now.replace(month=month, day=day, hour=hour, minute=minute, 
                             second=0, microsecond=0)
        
        if target < now:
            target = target.replace(year=now.year + 1)
            
        return target
    except Exception:
        return None

def get_remaining_time(deadline):
    """Hitung sisa waktu dengan format keren"""
    now = datetime.now(JAKARTA_TZ)
    delta = deadline - now
    
    if delta.total_seconds() < 0:
        return "🚨 <b>TELAT MEOW!</b>"
    
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    
    if days > 0:
        return f"⏳ {days}d {hours}j {minutes}m"
    elif hours > 0:
        return f"⏰ {hours}j {minutes}m"
    else:
        return f"⚡ {minutes}m"

# ==========================================
# KEYBOARD GENERATORS
# ==========================================
def get_home_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Tambah Tugas", callback_data='menu_tambah')],
        [InlineKeyboardButton("📅 Jadwal Harian", callback_data='menu_jadwal'),
         InlineKeyboardButton("📊 Daftar Tugas", callback_data='menu_lihat')],
        [InlineKeyboardButton("🗑️ Hapus Tugas", callback_data='menu_hapus'),
         InlineKeyboardButton("🔥 Reset Semua", callback_data='menu_reset')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_days_keyboard():
    keyboard = []
    for i in range(0, len(DAYS), 2):
        row = [InlineKeyboardButton(DAYS[i], callback_data=f"day_{DAYS[i]}")]
        if i + 1 < len(DAYS):
            row.append(InlineKeyboardButton(DAYS[i + 1], callback_data=f"day_{DAYS[i + 1]}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data='back_main')])
    return InlineKeyboardMarkup(keyboard)

def get_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("👤 Mandiri", callback_data='type_mandiri'),
         InlineKeyboardButton("👥 Kelompok", callback_data='type_kelompok')],
        [InlineKeyboardButton("🔙 Kembali", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_delete_keyboard(tugas):
    keyboard = [[InlineKeyboardButton(f"🗑️ {t['nama']}", callback_data=f"del_t_{t['nama']}")] 
                for t in tugas]
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data='back_main')])
    return InlineKeyboardMarkup(keyboard)

def get_done_keyboard(tugas):
    keyboard = [[InlineKeyboardButton(f"✅ {t['nama']}", callback_data=f"done_{t['nama']}")] 
                for t in tugas]
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data='back_main')])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>╭━━━〔 🤖 CATHELP 〕━━━╮</b>\n\n"
        "Halo meow 😼✨ <b>Partner belajar anti-mager!</b>\n\n"
        "<b>🔥 Aku bisa:</b>\n"
        "• Spam reminder pas deadline supaya kamu nggak lupa\n"
        "• Reminder jadwal harian otomatis\n"
        "• Nyimpen jadwal harian\n"
        "• Nyatet tugas\n\n"
        "<i>Gak ngerjain tugas? Siap-siap kena <b>CAKAR</b>! 😾</i>"
    )
    keyboard = get_home_keyboard()
    
    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'menu_tambah':
        await query.edit_message_text("📝 Okee meow~ Ketik <b>Nama Tugasnya</b> dulu ya 😼")
        context.user_data['state'] = 'WAIT_TASK_NAME'

    elif query.data == 'menu_jadwal':
        await query.edit_message_text("📅 Pilih hari buat jadwal rutinnya~", reply_markup=get_days_keyboard())

    elif query.data.startswith('day_'):
        day = query.data.split('_', 1)[1]
        context.user_data['temp_day'] = day
        await query.edit_message_text(f"📅 Jadwal hari <b>{day}</b>\n\nKetik nama kegiatannya meow 😼")
        context.user_data['state'] = 'WAIT_JADWAL_NAME'

    elif query.data == 'menu_lihat':
        await show_tasks(query, context)

    elif query.data == 'menu_hapus':
        tugas = context.user_data.get('tugas', [])
        if not tugas:
            await query.edit_message_text("📭 Belum ada tugas buat dihapus meow 😿", reply_markup=get_home_keyboard())
        else:
            await query.edit_message_text("🗑️ Pilih tugas yang mau di-yeet:", reply_markup=get_delete_keyboard(tugas))

    elif query.data.startswith('del_t_'):
        nama = query.data.split('_', 2)[2]
        context.user_data['tugas'] = [t for t in context.user_data.get('tugas', []) if t['nama'] != nama]
        for job in context.job_queue.get_jobs_by_name(nama):
            job.schedule_removal()
        await query.edit_message_text(f"🗑️ <b>{nama}</b> udah aku <b>BANTAI</b> meow! 😼🔥", reply_markup=get_home_keyboard())

    elif query.data == 'menu_reset':
        context.user_data.clear()
        for job in context.job_queue.jobs():
            job.schedule_removal()
        await query.edit_message_text("💥 <b>SEMUA DATA DIBANTAI TOTAL!</b>\n\nMulai dari nol lagi meow! 😼🔥", reply_markup=get_home_keyboard())

    elif query.data.startswith('type_'):
        tipe = query.data.split('_')[1]
        context.user_data['temp_type'] = tipe
        await query.edit_message_text("📅 Ketik <b>Tanggal Deadline</b>\nFormat: <code>DD-MM</code>\n\nContoh: <code>25-12</code>")
        context.user_data['state'] = 'WAIT_TASK_DATE'

    elif query.data.startswith('done_'):
        nama = query.data.split('_', 1)[1]
        context.user_data['tugas'] = [t for t in context.user_data.get('tugas', []) if t['nama'] != nama]
        for job in context.job_queue.get_jobs_by_name(nama):
            job.schedule_removal()
        await query.edit_message_text(
            f"🎉 <b>MANTAP BANGET MEOW!</b> 🏆\n\n"
            f"<b>{nama}</b> <i>SELESAI!</i>\n\n"
            f"Aku bangga banget sama kamu meow! 💯🐾✨", 
            reply_markup=get_home_keyboard()
        )

    elif query.data == 'back_main':
        await start(update, context)

async def show_tasks(query, context):
    tugas = context.user_data.get('tugas', [])
    jadwal = context.user_data.get('jadwal', [])
    now = datetime.now(JAKARTA_TZ)

    text = "<b>📚 TUGAS AKTIF</b>\n\n"
    
    if tugas:
        for t in tugas:
            deadline = t['deadline_obj']
            status = get_remaining_time(deadline)
            progress = min(100, max(0, int(100 * (deadline - now).total_seconds() / (24*3600))))
            
            text += (
                f"📝 <b>{t['nama']}</b>\n"
                f"📅 <code>{deadline.strftime('%d/%m/%Y %H:%M')}</code>\n"
                f"👥 {t['tipe']}\n"
                f"📊 {get_progress_bar(progress)} {status}\n\n"
            )
    else:
        text += "✅ Belum ada tugas! Kamu rajin banget meow 😎\n"

    text += "━━━━━━━━━━━━━━━━━━━━━\n"
    text += "<b>📅 JADWAL HARIAN</b>\n\n"
    
    if jadwal:
        today = datetime.now(JAKARTA_TZ).strftime("%A")
        hari_id = DAYS.index(today) if today in DAYS else 0
        
        for j in jadwal:
            text += f"📍 {j['hari']} - {j['nama']} (<code>{j['jam']}</code>)\n"
    else:
        text += "📭 Jadwal masih kosong meow\n"
    
    await query.edit_message_text(text, reply_markup=get_home_keyboard())

# ==========================================
# STATE MACHINE LOGIC
# ==========================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    if not state:
        return
        
    txt = update.message.text.strip()

    if state == 'WAIT_TASK_NAME':
        context.user_data['temp_name'] = txt
        await update.message.reply_text(
            f"📝 Tugas <b>{txt}</b> noted!\n\n"
            "👥 Tugasnya mandiri apa kelompok?", 
            reply_markup=get_type_keyboard()
        )

    elif state == 'WAIT_TASK_DATE':
        if '-' not in txt or len(txt.split('-')) != 2:
            await update.message.reply_text("❌ Format salah! Pake <code>DD-MM</code> meow.\nContoh: <code>25-12</code>")
            return
        context.user_data['temp_date'] = txt
        await update.message.reply_text("⏰ Ketik <b>Jam Deadline</b>\nFormat: <code>HH:MM</code>\nContoh: <code>15:30</code>")
        context.user_data['state'] = 'WAIT_TASK_TIME'

    elif state == 'WAIT_TASK_TIME':
        deadline_obj = parse_target_datetime(context.user_data['temp_date'], txt)
        if not deadline_obj:
            await update.message.reply_text("❌ Input ngaco bro! Coba lagi meow.")
            return

        nama = context.user_data['temp_name']
        tipe = context.user_data['temp_type']
        
        new_task = {
            'nama': nama, 
            'tipe': "👤 Mandiri" if tipe == "mandiri" else "👥 Kelompok", 
            'deadline_obj': deadline_obj
        }
        
        if 'tugas' not in context.user_data:
            context.user_data['tugas'] = []
        context.user_data['tugas'].append(new_task)

        # JADWAL SPAM BRUTAL: 1 jam sebelum -> setiap 3 menit setelah deadline
        one_hour_before = deadline_obj - timedelta(hours=1)
        context.job_queue.run_once(
            pre_deadline_warning, 
            when=one_hour_before, 
            chat_id=update.effective_chat.id, 
            name=f"warn_{nama}",
            data={'nama': nama}
        )
        
        # Main deadline trigger
        context.job_queue.run_once(
            trigger_deadline, 
            when=deadline_obj, 
            chat_id=update.effective_chat.id, 
            name=nama,
            data={'nama': nama}
        )

        await update.message.reply_text(
            f"✅ <b>TUGAS {nama.upper()} DISIMPAN!</b> 🎯\n\n"
            f"📝 <b>{nama}</b>\n"
            f"⏰ <code>{deadline_obj.strftime('%d/%m/%Y %H:%M')}</code>\n"
            f"👥 {new_task['tipe']}\n\n"
            f"<i>🚨 SPAM MODE AKTIF!</i>",
            reply_markup=get_home_keyboard()
        )
        context.user_data['state'] = None

    elif state == 'WAIT_JADWAL_NAME':
        context.user_data['temp_j_name'] = txt
        await update.message.reply_text(f"⏰ Jam kegiatannya? (Contoh: <code>07:00</code>)")
        context.user_data['state'] = 'WAIT_JADWAL_TIME'

    elif state == 'WAIT_JADWAL_TIME':
        new_jadwal = {
            'hari': context.user_data['temp_day'], 
            'nama': context.user_data['temp_j_name'], 
            'jam': txt
        }
        if 'jadwal' not in context.user_data:
            context.user_data['jadwal'] = []
        context.user_data['jadwal'].append(new_jadwal)
        
        await update.message.reply_text(
            f"✅ <b>JADWAL ROUTIN DISIMPAN!</b>\n\n"
            f"📅 {context.user_data['temp_day']} - {txt}\n"
            f"📝 {context.user_data['temp_j_name']}",
            reply_markup=get_home_keyboard()
        )
        context.user_data['state'] = None

async def pre_deadline_warning(context: ContextTypes.DEFAULT_TYPE):
    """Warning 1 jam sebelum deadline"""
    job = context.job
    nama = job.data['nama']
    kb = [[InlineKeyboardButton("✅ Sudah Selesai", callback_data=f"done_{nama}")]]
    
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"⚠️ <b>1 JAM LAGI!</b> Tugas <b>{nama}</b> deadline-nya MEOW! Siap-siap! ⏰🔥",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def trigger_deadline(context: ContextTypes.DEFAULT_TYPE):
    """Trigger spam hell pas deadline"""
    job = context.job
    nama = job.data['nama']
    kb = [[InlineKeyboardButton("✅ Sudah Selesai", callback_data=f"done_{nama}")]]
    
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"🚨 <b>DEADLINE {nama.upper()} TELAH TIBA!</b>\n\n"
             f"Kerjain SEKARANG atau aku marah! 😾💥",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    
    # SPAM EVERY 3 MINUTES (180 detik)
    context.job_queue.run_repeating(
        execute_spam, 
        interval=180, 
        first=0, 
        chat_id=job.chat_id, 
        name=f"spam_{nama}",
        data={'nama': nama, 'count': 0}
    )

async def execute_spam(context: ContextTypes.DEFAULT_TYPE):
    """Execute spam message random"""
    job = context.job
    count = job.data['count'] + 1
    job.data['count'] = count
    
    msg = random.choice(SPAM_MESSAGES).format(nama=job.data['nama'])
    kb = [[InlineKeyboardButton("✅ Sudah Selesai", callback_data=f"done_{job.data['nama']}")]]
    
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"🚨 <b>SPAM #{count} - {job.data['nama'].upper()}</b>\n\n{msg}",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ==========================================
# DAILY SCHEDULE REMINDER
# ==========================================
async def daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Kirim reminder jadwal harian jam 6 pagi"""
    job = context.job
    now = datetime.now(JAKARTA_TZ)
    today = now.strftime("%A")
    hari = DAYS[now.weekday()]
    
    jadwal = job.data.get('jadwal', {}).get(hari, [])
    if jadwal:
        text = f"🌅 <b>HARI INI {hari.upper()}</b>\n\n"
        for j in jadwal:
            text += f"📅 {j['jam']} - {j['nama']}\n"
        text += "\nJangan lupa ya meow! 😼❤️"
        
        await context.bot.send_message(chat_id=job.chat_id, text=text)

# ==========================================
# MAIN
# ==========================================
def main():
    persistence = PicklePersistence(filepath="cathelp_data.pickle")
    app = Application.builder().token(TOKEN).persistence(persistence).defaults(defaults).build()

    # Daily reminder jam 6 pagi
    app.job_queue.run_daily(
        daily_reminder,
        time=datetime.time(hour=6, minute=0, tzinfo=JAKARTA_TZ),
        data={'jadwal': DAYS}
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 CATHELP AKTIF! 🔥")
    print("📱 Bot siap")
    
    app.run_polling()

if __name__ == '__main__':
    main()