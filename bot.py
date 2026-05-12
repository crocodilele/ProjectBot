import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = "8747562941:AAEGyf4mO-6bsEYcBbqfA0Apv96eDwTkc_M"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# =========================
# KEYBOARD
# =========================

def get_home_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Tambah Tugas", callback_data='menu_tambah')],
        [InlineKeyboardButton("📅 Jadwal Harian", callback_data='menu_jadwal')],
        [InlineKeyboardButton("📚 Semua Tugas", callback_data='menu_lihat')],
        [InlineKeyboardButton("🗑️ Hapus Data", callback_data='menu_hapus')],
        [InlineKeyboardButton("💥 Reset Semua", callback_data='menu_reset')],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_days_keyboard():
    keyboard = []

    for i in range(0, len(DAYS), 2):
        row = [InlineKeyboardButton(DAYS[i], callback_data=f"day_{DAYS[i]}")]

        if i + 1 < len(DAYS):
            row.append(InlineKeyboardButton(DAYS[i + 1], callback_data=f"day_{DAYS[i + 1]}"))

        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ Balik Menu", callback_data='back_main')])

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
╭━━━〔 🤖 CATHELP AI 〕━━━╮

Halo meow 😼✨
Aku CatHelp AI, partner belajar anti lupa tugas 📚⚡

Aku bisa:
📝 Nyatet tugas
⏰ Spam reminder brutal
📅 Nyimpen jadwal sekolah
🔥 Ngingetin sampe tugas kelar

Tekan menu di bawah yaa 👇
"""

    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=get_home_keyboard()
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=get_home_keyboard()
        )


# =========================
# CALLBACK BUTTON
# =========================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    # ================= MENU TAMBAH =================

    if query.data == 'menu_tambah':

        await query.edit_message_text(
            "📝 Okee meow~\n\nKetik nama tugasnya dulu ya 😼"
        )

        context.user_data['state'] = 'WAIT_TASK_NAME'

    # ================= MENU JADWAL =================

    elif query.data == 'menu_jadwal':

        await query.edit_message_text(
            "📅 Pilih hari buat jadwalnyaa~",
            reply_markup=get_days_keyboard()
        )

    # ================= PILIH HARI =================

    elif query.data.startswith('day_'):

        day = query.data.split('_')[1]

        context.user_data['temp_day'] = day

        await query.edit_message_text(
            f"📅 Jadwal hari {day}\n\nKetik nama kegiatannya 😼"
        )

        context.user_data['state'] = 'WAIT_JADWAL_NAME'

    # ================= LIHAT DATA =================

    elif query.data == 'menu_lihat':

        tugas = context.user_data.get('tugas', [])
        jadwal = context.user_data.get('jadwal', [])

        text = "📚 DAFTAR TUGAS KAMU\n\n"

        if tugas:
            for t in tugas:
                text += (
                    f"📝 {t['nama']}\n"
                    f"📅 {t['tgl']}\n"
                    f"⏰ {t['jam']}\n"
                    f"👥 {t['tipe']}\n\n"
                )
        else:
            text += "Belum ada tugas bestie 😭\n"

        text += "\n━━━━━━━━━━━━━━\n"
        text += "📅 JADWAL HARIAN\n\n"

        if jadwal:
            for j in jadwal:
                text += (
                    f"📌 {j['hari']} - {j['nama']} ({j['jam']})\n"
                )
        else:
            text += "Belum ada jadwal 😭"

        await query.edit_message_text(
            text,
            reply_markup=get_home_keyboard()
        )

    # ================= HAPUS =================

    elif query.data == 'menu_hapus':

        tugas = context.user_data.get('tugas', [])
        jadwal = context.user_data.get('jadwal', [])

        kb = []

        for t in tugas:
            kb.append([
                InlineKeyboardButton(
                    f"❌ {t['nama']}",
                    callback_data=f"del_t_{t['nama']}"
                )
            ])

        for j in jadwal:
            kb.append([
                InlineKeyboardButton(
                    f"❌ {j['nama']}",
                    callback_data=f"del_j_{j['nama']}"
                )
            ])

        kb.append([
            InlineKeyboardButton(
                "⬅️ Balik",
                callback_data='back_main'
            )
        ])

        await query.edit_message_text(
            "🗑️ Pilih yang mau dihapus",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # ================= DELETE =================

    elif query.data.startswith('del_'):

        _, tipe, nama = query.data.split('_')

        if tipe == 't':
            context.user_data['tugas'] = [
                t for t in context.user_data.get('tugas', [])
                if t['nama'] != nama
            ]

        else:
            context.user_data['jadwal'] = [
                j for j in context.user_data.get('jadwal', [])
                if j['nama'] != nama
            ]

        jobs = context.job_queue.get_jobs_by_name(nama)

        for job in jobs:
            job.schedule_removal()

        await query.edit_message_text(
            f"🗑️ {nama} berhasil dihapus bestie 😼",
            reply_markup=get_home_keyboard()
        )

    # ================= RESET =================

    elif query.data == 'menu_reset':

        context.user_data.clear()

        for job in context.job_queue.jobs():
            job.schedule_removal()

        await query.edit_message_text(
            "💥 Semua data berhasil dibantai 😼🔥",
            reply_markup=get_home_keyboard()
        )

    # ================= TIPE TUGAS =================

    elif query.data.startswith('type_'):

        tipe = query.data.split('_')[1]

        context.user_data['temp_type'] = tipe

        await query.edit_message_text(
            "📅 Ketik deadline\nContoh: 25-12"
        )

        context.user_data['state'] = 'WAIT_TASK_DATE'

    # ================= BACK =================

    elif query.data == 'back_main':

        await start(update, context)

    # ================= DONE =================

    elif query.data.startswith('done_'):

        nama = query.data.split('_')[1]

        jobs = context.job_queue.get_jobs_by_name(nama)

        for job in jobs:
            job.schedule_removal()

        context.user_data['tugas'] = [
            t for t in context.user_data.get('tugas', [])
            if t['nama'] != nama
        ]

        context.user_data['jadwal'] = [
            j for j in context.user_data.get('jadwal', [])
            if j['nama'] != nama
        ]

        await query.edit_message_text(
            f"""
🎉 YEEAAAYY!!

Tugas:
✅ {nama}

BERHASIL SELESAI 😼💝

Aku bangga sama kamu meow 💯🐾
""",
            reply_markup=get_home_keyboard()
        )


# =========================
# HANDLE TEXT
# =========================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    state = context.user_data.get('state')

    if not state:
        return

    txt = update.message.text

    # ================= NAMA TUGAS =================

    if state == 'WAIT_TASK_NAME':

        context.user_data['temp_name'] = txt

        kb = [[
            InlineKeyboardButton(
                "👤 Mandiri",
                callback_data="type_MANDIRI"
            ),

            InlineKeyboardButton(
                "👥 Kelompok",
                callback_data="type_KELOMPOK"
            )
        ]]

        await update.message.reply_text(
            "📚 Tugasnya mandiri apa kelompok? 🐾",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # ================= TANGGAL =================

    elif state == 'WAIT_TASK_DATE':

        context.user_data['temp_date'] = txt

        await update.message.reply_text(
            "⏰ Sekarang ketik jam deadline\nContoh: 15:30"
        )

        context.user_data['state'] = 'WAIT_TASK_TIME'

    # ================= JAM TUGAS =================

    elif state == 'WAIT_TASK_TIME':

        await set_alarm(
            update,
            context,
            txt,
            context.user_data['temp_name'],
            f"{context.user_data['temp_date']} ({context.user_data['temp_type']})",
            True
        )

    # ================= NAMA JADWAL =================

    elif state == 'WAIT_JADWAL_NAME':

        context.user_data['temp_j_name'] = txt

        await update.message.reply_text(
            f"⏰ Jam kegiatan hari {context.user_data['temp_day']}?"
        )

        context.user_data['state'] = 'WAIT_JADWAL_TIME'

    # ================= JAM JADWAL =================

    elif state == 'WAIT_JADWAL_TIME':

        await set_alarm(
            update,
            context,
            txt,
            context.user_data['temp_j_name'],
            context.user_data['temp_day'],
            False
        )


# =========================
# SET ALARM
# =========================

# =========================
# SET ALARM
# =========================

async def set_alarm(update, context, jam, nama, info, is_tugas):

    try:

        # ================= FIX FORMAT JAM =================

        jam = jam.strip()

        if ":" not in jam:
            raise ValueError("Format jam salah")

        h, m = map(int, jam.split(":"))

        if h < 0 or h > 23 or m < 0 or m > 59:
            raise ValueError("Jam tidak valid")

        now = datetime.now()

        target = now.replace(
            hour=h,
            minute=m,
            second=0,
            microsecond=0
        )

        diff = (target - now).total_seconds()

        if diff < 0:
            diff += 86400

        key = 'tugas' if is_tugas else 'jadwal'

        if key not in context.user_data:
            context.user_data[key] = []

        entry = {
            'nama': nama,
            'jam': jam
        }

        if is_tugas:
            entry['tgl'] = info.split(' (')[0]
            entry['tipe'] = info.split('(')[1].replace(')', '')
        else:
            entry['hari'] = info

        context.user_data[key].append(entry)

        # ================= REMINDER SPAM =================
        # spam tiap 5 menit maksimal 15x

        context.job_queue.run_repeating(
            alarm_msg,
            interval=300,
            first=diff,
            chat_id=update.effective_chat.id,
            name=nama,
            data={
                'nama': nama,
                'count': 0,
                'max': 15
            }
        )

        await update.message.reply_text(
            f"""
✅ TUGAS BERHASIL DISIMPAN

📝 {nama}
⏰ {jam}

🚨 Reminder brutal sudah aktif meow 😼🔥
Aku bakal spam sampe tugasnya kelar 😾
""",
            reply_markup=get_home_keyboard()
        )

        context.user_data['state'] = None

    except Exception as e:

        print(e)

        await update.message.reply_text(
            """
❌ Format jam salah meow 😿

Contoh yang bener:
⏰ 15:30
⏰ 07:05
"""
        )


# =========================
# REMINDER MESSAGE
# =========================

async def alarm_msg(context: ContextTypes.DEFAULT_TYPE):

    job = context.job

    job.data['count'] += 1

    count = job.data['count']
    max_spam = job.data['max']
    nama = job.data['nama']

    # stop kalau udah max
    if count > max_spam:
        job.schedule_removal()
        return

    kb = [[
        InlineKeyboardButton(
            "✅ Udah Kelar Cuy",
            callback_data=f"done_{nama}"
        )
    ]]

    # ================= PESAN LUCU =================

    messages = [
        f"🚨 WOI \n\nTugas {nama} belum dikerjain meow 😸",
        
        f"📚 {nama} masih hidup di daftar tugas...\nKapan mau dikerjain? 😿",
        
        f"⚠️ Reminder ke-{count}\n\n{nama} nangis minta diselesaikan 😼",
        
        f"🔥 HELLOW\n\nDeadline {nama} makin dekat tau",
        
        f"💀 Tugas {nama} mulai mengancam masa depanmu 😿",
        
        f"😼 CatHelp AI datang membawa reminder brutal 😾",
        
        f"📢 Fokus dulu meow\n{nama} belum selesaiii",
        
        f"⚡ AYO GERAKK\n\n{nama} jangan sampe telat",
        
        f"🗿 Diam bukan solusi\nKerjakan {nama} sekarang",
        
        f"🚨 SPAM REMINDER MODE AKTIF\n\n{nama} belum kelar MEOW!"
    ]

    msg = messages[count % len(messages)]

    # tambahan cuma 3x
    if count <= 3:
        msg += "\n\n⏳ Aku bakal balik lagi 😼"

    msg += f"\n\n📌 Reminder: {count}/{max_spam}"

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=msg,
        reply_markup=InlineKeyboardMarkup(kb)
    )


# =========================
# MAIN
# =========================

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(handle_callback))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    print("BOT BERJALAN 😼🔥")

    app.run_polling()


if __name__ == '__main__':
    main()