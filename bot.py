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

# ==========================================
# KONFIGURASI DAN GLOBAL DEFAULTS
# ==========================================
# Ganti TOKEN di bawah dengan token asli dari @BotFather
TOKEN = "8747562941:AAEGyf4mO-6bsEYcBbqfA0Apv96eDwTkc_M"
JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

# Mengatur Defaults: Pesan otomatis HTML & Waktu otomatis Jakarta 
defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=JAKARTA_TZ)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

DAYS =

# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def get_progress_bar(percent):
    """Menghasilkan bar visual loading menggunakan Unicode blok [40]"""
    length = 10
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percent}%"

def parse_target_datetime(date_str, time_str):
    """Mengonversi input DD-MM dan HH:MM ke objek datetime aware [24, 52]"""
    try:
        now = datetime.now(JAKARTA_TZ)
        day, month = map(int, date_str.split('-'))
        hour, minute = map(int, time_str.split(':'))
        
        # Inisialisasi target untuk tahun ini
        target = now.replace(month=month, day=day, hour=hour, minute=minute, 
                             second=0, microsecond=0)
        
        # Jika waktu target ternyata sudah lewat dari sekarang, asumsikan untuk tahun depan [25]
        if target < now:
            target = target.replace(year=now.year + 1)
            
        return target
    except Exception as e:
        logging.error(f"Error parsing date: {e}")
        return None

# ==========================================
# KEYBOARD GENERATORS
# ==========================================
def get_home_keyboard():
    keyboard =,
       ,
       
    return InlineKeyboardMarkup(keyboard)

def get_days_keyboard():
    keyboard =
    for i in range(0, len(DAYS), 2):
        row =, callback_data=f"day_{DAYS[i]}")]
        if i + 1 < len(DAYS):
            row.append(InlineKeyboardButton(DAYS[i + 1], callback_data=f"day_{DAYS[i + 1]}"))
        keyboard.append(row)
    keyboard.append()
    return InlineKeyboardMarkup(keyboard)

# ==========================================
# COMMAND & CALLBACK HANDLERS
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler perintah /start - Entry point utama [53]"""
    text = (
        "<b>╭━━━〔 🤖 CATHELP AI PRO 〕━━━╮</b>\n\n"
        "Halo meow 😼✨ Aku partner belajar anti-prokrastinasi paling brutal.\n\n"
        "<b>Apa yang bisa gue lakuin?</b>\n"
        "• Nyatet tugas & deadline presisi\n"
        "• Spam reminder brutal kalo lu mager\n"
        "• Tracking progress sisa waktu lu\n\n"
        "<i>Gak ngerjain tugas? Siap-siap kena mental meow!</i> 😾"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=get_home_keyboard())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=get_home_keyboard())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengelola interaksi tombol inline [45]"""
    query = update.callback_query
    await query.answer()

    if query.data == 'menu_tambah':
        await query.edit_message_text("📝 Okee meow~ Ketik <b>Nama Tugasnya</b> dulu ya 😼")
        context.user_data['state'] = 'WAIT_TASK_NAME'

    elif query.data == 'menu_jadwal':
        await query.edit_message_text("📅 Pilih hari buat jadwalnyaa~", reply_markup=get_days_keyboard())

    elif query.data.startswith('day_'):
        day = query.data.split('_')
        context.user_data['temp_day'] = day
        await query.edit_message_text(f"📅 Jadwal hari <b>{day}</b>\n\nKetik nama kegiatannya meow 😼")
        context.user_data['state'] = 'WAIT_JADWAL_NAME'

    elif query.data == 'menu_lihat':
        tugas = context.user_data.get('tugas',)
        jadwal = context.user_data.get('jadwal',)
        now = datetime.now(JAKARTA_TZ)

        text = "<b>📚 DAFTAR TUGAS AKTIF</b>\n\n"
        if tugas:
            for t in tugas:
                # Kalkulasi sisa waktu secara dinamis
                deadline = t['deadline_obj']
                delta = deadline - now
                if delta.total_seconds() < 0:
                    status = "🚨 <b>OVERDUE NJIR!</b>"
                else:
                    days = delta.days
                    hours, rem = divmod(delta.seconds, 3600)
                    minutes, _ = divmod(rem, 60)
                    status = f"⏳ Sisa {days}h {hours}j {minutes}m"
                
                text += (
                    f"📌 <b>{t['nama']}</b>\n"
                    f"📅 Deadline: <code>{deadline.strftime('%d %b %Y, %H:%M')}</code>\n"
                    f"👥 Tipe: {t['tipe']}\n"
                    f"📊 Status: {status}\n\n"
                )
        else:
            text += "Belum ada tugas, tumben lu rajin anjir 😭\n"

        text += "<b>━━━━━━━━━━━━━━</b>\n"
        text += "<b>📅 JADWAL HARIAN</b>\n\n"
        if jadwal:
            for j in jadwal:
                text += f"📍 {j['hari']} - {j['nama']} (<code>{j['jam']}</code>)\n"
        else:
            text += "Jadwal kosong meow."
        
        await query.edit_message_text(text, reply_markup=get_home_keyboard())

    elif query.data == 'menu_hapus':
        tugas = context.user_data.get('tugas',)
        kb =
        for t in tugas:
            kb.append(}", callback_data=f"del_t_{t['nama']}")])
        kb.append()
        await query.edit_message_text("🗑️ Pilih yang mau di-yeet dari memori meow:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith('del_'):
        _, tipe, nama = query.data.split('_')
        context.user_data['tugas'] = [t for t in context.user_data.get('tugas',) if t['nama']!= nama]
        
        # Batalkan pekerjaan spam yang sedang berjalan [30]
        current_jobs = context.job_queue.get_jobs_by_name(nama)
        for job in current_jobs:
            job.schedule_removal()
            
        await query.edit_message_text(f"🗑️ <b>{nama}</b> udah gue apus dari otak gue meow! 😼", reply_markup=get_home_keyboard())

    elif query.data == 'menu_reset':
        context.user_data.clear()
        for job in context.job_queue.jobs():
            job.schedule_removal()
        await query.edit_message_text("💥 <b>SEMUA DATA BERHASIL DIBANTAI!</b> 😼🔥", reply_markup=get_home_keyboard())

    elif query.data.startswith('type_'):
        tipe = query.data.split('_')
        context.user_data['temp_type'] = tipe
        await query.edit_message_text("📅 Ketik <b>Tanggal Deadline</b> meow\nFormat: <code>DD-MM</code> (Contoh: 15-05)")
        context.user_data['state'] = 'WAIT_TASK_DATE'

    elif query.data == 'back_main':
        await start(update, context)

    elif query.data.startswith('done_'):
        nama = query.data.split('_')
        # Hapus data tugas
        context.user_data['tugas'] = [t for t in context.user_data.get('tugas',) if t['nama']!= nama]
        # Matikan spam pengingat [31]
        current_jobs = context.job_queue.get_jobs_by_name(nama)
        for job in current_jobs:
            job.schedule_removal()

        await query.edit_message_text(
            f"🎉 <b>YEEAAAAYY!!</b>\n\nTugas <b>{nama}</b> berhasil kelar.\n"
            f"Gitu dong bestie, aku bangga sama kamu meow! 💯🐾",
            reply_markup=get_home_keyboard()
        )

# ==========================================
# TEXT INPUT STATE MACHINE
# ==========================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    if not state: return
    txt = update.message.text

    if state == 'WAIT_TASK_NAME':
        context.user_data['temp_name'] = txt
        kb =]
        await update.message.reply_text("👥 Tugasnya mandiri apa kelompok anjir? 🐾", reply_markup=InlineKeyboardMarkup(kb))

    elif state == 'WAIT_TASK_DATE':
        if '-' not in txt:
            await update.message.reply_text("❌ Salah format njir! Pake <code>DD-MM</code> (Contoh: 25-12)")
            return
        context.user_data['temp_date'] = txt
        await update.message.reply_text("⏰ Sekarang ketik <b>Jam Deadline</b> meow\nFormat: <code>HH:MM</code> (Contoh: 15:30)")
        context.user_data['state'] = 'WAIT_TASK_TIME'

    elif state == 'WAIT_TASK_TIME':
        if ':' not in txt:
            await update.message.reply_text("❌ Jam-nya yang bener dong! Contoh <code>13:00</code>")
            return
            
        deadline_obj = parse_target_datetime(context.user_data['temp_date'], txt)
        if not deadline_obj:
            await update.message.reply_text("❌ Input lu ngaco meow, coba lagi.")
            return

        nama = context.user_data['temp_name']
        tipe = context.user_data['temp_type']
        
        # Simpan tugas baru
        new_task = {
            'nama': nama,
            'tipe': tipe,
            'deadline_obj': deadline_obj
        }
        if 'tugas' not in context.user_data: context.user_data['tugas'] =
        context.user_data['tugas'].append(new_task)

        # Daftarkan Alarm Tahap 1: Tepat saat deadline 
        context.job_queue.run_once(
            trigger_deadline_alarm, 
            when=deadline_obj, 
            chat_id=update.effective_chat.id, 
            name=nama, 
            data={'nama': nama}
        )

        await update.message.reply_text(
            f"✅ <b>TUGAS BERHASIL DISIMPAN!</b>\n\n"
            f"📝 <b>{nama}</b>\n"
            f"⏰ Deadline: {deadline_obj.strftime('%d %b %Y, %H:%M')}\n\n"
            f"<i>Mode brutal aktif. Gue spam sampe lu kelar meow!</i> 🔥",
            reply_markup=get_home_keyboard()
        )
        context.user_data['state'] = None

    elif state == 'WAIT_JADWAL_NAME':
        context.user_data['temp_j_name'] = txt
        await update.message.reply_text(f"⏰ Jam kegiatannya jam berapa meow? (Contoh <code>07:00</code>)")
        context.user_data['state'] = 'WAIT_JADWAL_TIME'

    elif state == 'WAIT_JADWAL_TIME':
        new_j = {'hari': context.user_data['temp_day'], 'nama': context.user_data['temp_j_name'], 'jam': txt}
        if 'jadwal' not in context.user_data: context.user_data['jadwal'] =
        context.user_data['jadwal'].append(new_j)
        await update.message.reply_text("✅ Jadwal rutin kesimpen meow!", reply_markup=get_home_keyboard())
        context.user_data['state'] = None

# ==========================================
# ALARM & SPAM REMINDER ENGINE
# ==========================================
async def trigger_deadline_alarm(context: ContextTypes.DEFAULT_TYPE):
    """Alarm awal saat deadline tercapai - Mengaktifkan mode spam berulang [13]"""
    job = context.job
    nama = job.data['nama']
    
    kb =]
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"🚨 <b>WOI WOI WOI!</b>\n\nTugas <b>{nama}</b> waktunya udah abis meow!\nCepetan kerjain atau gue spam sampe gila! 😾🔥",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    
    # Inisialisasi Spam Tahap 2: Setiap 5 menit 
    context.job_queue.run_repeating(
        execute_spam_cycle,
        interval=300, # 5 menit
        first=300, 
        chat_id=job.chat_id,
        name=nama,
        data={'nama': nama, 'count': 0}
    )

async def execute_spam_cycle(context: ContextTypes.DEFAULT_TYPE):
    """Siklus spam berkelanjutan dengan pesan acak yang brutal [30]"""
    job = context.job
    job.data['count'] += 1
    count = job.data['count']
    nama = job.data['nama']
    
    # Kumpulan pesan brutal 
    messages =
    
    msg = messages[count % len(messages)]
    kb =]
    
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"🚨 <b>SPAM REMINDER BRUTAL</b>\n\n{msg}\n\n📌 <i>Spam counter: {count}</i>",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ==========================================
# MAIN APPLICATION SETUP
# ==========================================
def main():
    """Inisialisasi bot dengan persistensi data [14, 34]"""
    # Menggunakan PicklePersistence agar data tidak hilang saat restart server
    persistence = PicklePersistence(filepath="cathelp_storage.pickle")
    
    # Membangun aplikasi dengan Defaults & Persistence [5, 10]
    app = (
        Application.builder()
       .token(TOKEN)
       .persistence(persistence)
       .defaults(defaults)
       .build()
    )

    # Registrasi handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 CATHELP AI PRO AKTIF & SIAP MENERKAM TUGAS LU! 😼🔥")
    app.run_polling()

if __name__ == '__main__':
    main()