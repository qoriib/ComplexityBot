import time
import argparse
from utils.api import Api
from bot.greedy_bot import get_next_move
from utils.models import Bot

# === PARSING ARGUMEN TERMINAL ===
# Digunakan untuk menjalankan bot dengan konfigurasi berbeda dari terminal
parser = argparse.ArgumentParser(description="Complexity bot")
parser.add_argument("--email", default="bot@student.itera.ac.id")  # Email bot
parser.add_argument("--password", default="123456")                # Password bot
parser.add_argument("--name", default="CBot")             # Nama bot (unik di board)
parser.add_argument("--team", default="etimo")                     # Nama tim bot
parser.add_argument("--url", default="http://localhost:3000/api")  # URL API
args = parser.parse_args()

# Simpan argumen ke variabel
EMAIL = args.email
PASSWORD = args.password
NAME = args.name
TEAM = args.team
BASE_URL = args.url

# === INISIALISASI OBJEK API ===
api = Api(BASE_URL)

# === LOGIN ATAU DAFTARKAN BOT ===
bot_id = api.bots_recover(EMAIL, PASSWORD)
if not bot_id:
    # Jika tidak bisa recover, daftar bot baru
    bot_obj = api.bots_register(NAME, EMAIL, PASSWORD, TEAM)
    if not bot_obj:
        print("[FATAL] Gagal mendaftar bot.")
        exit()
    bot_id = bot_obj.id
    print(f"[INFO] Bot baru terdaftar: {bot_id}")
else:
    print(f"[INFO] Bot ditemukan: {bot_id}")

# Buat objek bot untuk digunakan dalam pemrosesan logika
bot_data = Bot(name=NAME, email=EMAIL, id=bot_id)

# === DAPATKAN BOARD DAN GABUNG JIKA PERLU ===
boards = api.boards_list()
if not boards:
    print("[FATAL] Tidak ada board tersedia.")
    exit()

board_id = boards[0].id 
board_state = api.boards_get(board_id)

# Cek apakah bot sudah tergabung di board
if not any(b.properties.name == NAME for b in board_state.bots):
    # Jika belum, coba gabung ke board
    if not api.bots_join(bot_id, board_id):
        print("[FATAL] Gagal join board.")
        exit()
    print(f"[INFO] Bot '{NAME}' join board {board_id}")
else:
    print(f"[INFO] Bot '{NAME}' sudah di board {board_id}")

# Mengambil kondisi board terbaru
board_state = api.boards_get(board_id)

# === BOT LOOP ===
# Loop utama selama bot masih hidup di board
while True:
    try:
        # Dapatkan langkah selanjutnya dari strategi greedy
        move_result = get_next_move(board_state, bot_data)
        if move_result:
            move, target_pos = move_result
            print(f"[MOVE] {NAME} bergerak {move} ke {target_pos}")

            # Kirim perintah move ke server
            board_state = api.bots_move(bot_id, move)

            # Jika response kosong, artinya game over (bot sudah dikeluarkan dari board)
            if board_state is None:
                print("[INFO] Bot tidak lagi aktif. Permainan selesai.")
                break
        else:
            # Tidak ada langkah diperlukan, bot idle
            print("[INFO] Tidak ada langkah. Bot idle.")
            continue

        # Delay agar sesuai aturan board (minimum delay antar move)
        time.sleep((board_state.minimum_delay_between_moves / 1000))

    except Exception as e:
        # Penanganan exception umum, seperti koneksi gagal, dll
        break

print(f"[INFO] Selesai.")
