import random
from typing import Optional, Tuple
from utils.models import Board, Bot, Position, GameObject

# Fungsi untuk menentukan langkah berikutnya
def get_next_move(board: Board, my_bot_data: Bot) -> Optional[Tuple[str, int]]:
    # Ambil objek bot dari board
    my_bot: GameObject = board.get_bot(my_bot_data)

    # Tidak bisa bergerak jika bot tidak ditemukan
    if not my_bot or not my_bot.position:
        return None  

    # Posisi dan properti dasar dari bot
    my_pos = my_bot.position
    base_pos = my_bot.properties.base
    inventory = my_bot.properties.diamonds or 0
    max_inventory = my_bot.properties.inventory_size or 5

    # Hindari semua posisi teleport
    teleport_positions = {
        obj.position for obj in board.game_objects
        if obj.position and obj.type == "TeleportGameObject"
    }

    # === PRIORITAS 0: Pulang ke base jika inventori penuh ===
    if inventory >= max_inventory:
        if base_pos:
            if not positions_equal(my_pos, base_pos):
                direction = direction_towards(my_pos, base_pos, teleport_positions)
                if direction:
                    return direction, -1  # Menuju base
                else:
                    return random_move(my_pos, teleport_positions)  # Alternatif jika terhalang
            else:
                # Sudah di base tapi belum kosong, mungkin perlu waktu/trigger
                # Lakukan gerakan acak kecil untuk 'bangunkan' bot
                return random_move(my_pos, teleport_positions)
        return None

    # === PRIORITAS 1: Cari diamond terbaik yang kita lebih dekat dari bot lain ===
    target = find_best_diamond(
        board, my_pos, inventory, max_inventory, teleport_positions,
        prefer_closest=True, my_name=my_bot.properties.name
    )

    # === PRIORITAS 2: Jika tidak ada, ambil diamond terbaik tanpa mempertimbangkan kedekatan bot lain ===
    if not target:
        target = find_best_diamond(
            board, my_pos, inventory, max_inventory, teleport_positions,
            prefer_closest=False
        )

    # === PRIORITAS 3: Jika tetap tidak ada, lakukan gerakan acak (asal tidak masuk teleport) ===
    if target:
        direction, target_id = target
        return direction, target_id

    return random_move(my_pos, teleport_positions)  # -2 menandakan random step

# Fungsi untuk mencari diamond terbaik
def find_best_diamond(board, my_pos, inventory, max_inventory, avoid, prefer_closest=True, my_name=None):
    # Inisialisasi variabel untuk menyimpan diamond terbaik
    best_score = -1
    target_pos = None
    target_id = None

    # Iterasi semua objek di papan
    for obj in board.game_objects:
        # Lewati jika bukan diamond atau tidak memiliki posisi
        if obj.type != "DiamondGameObject" or not obj.position:
            continue

        pos = obj.position
        points = obj.properties.points if obj.properties else None

        # Lewati jika diamond tidak memiliki poin atau poin tidak valid
        if points is None or points <= 0:
            continue

        # Lewati jika diamond tidak muat di inventori
        if inventory + points > max_inventory:
            continue

        # Lewati jika sudah di posisi diamond
        if positions_equal(pos, my_pos):
            continue

        # Hitung jarak bot kita ke diamond ini
        my_dist = manhattan_distance(my_pos, pos)

        # === Cek apakah kita lebih dekat dari bot lain ===
        if prefer_closest and my_name:
            # Cek setiap bot lain
            for bot in board.bots:
                if not bot.position or bot.properties.name == my_name:
                    continue
                # Jika ada bot lain lebih dekat, diamond ini tidak dipilih
                if manhattan_distance(bot.position, pos) < my_dist:
                    break
            else:
                # Tidak ada bot lain lebih dekat: diamond ini kandidat
                score = points / (my_dist + 1)
                if score > best_score:
                    best_score = score
                    target_pos = pos
                    target_id = obj.id

        # === Alternatif: Ambil diamond terbaik tanpa cek kedekatan bot lain ===
        elif not prefer_closest:
            score = points / (my_dist + 1)
            if score > best_score:
                best_score = score
                target_pos = pos
                target_id = obj.id

    # Jika ditemukan diamond yang valid, kembalikan arahnya dan ID-nya
    if target_pos:
        direction = direction_towards(my_pos, target_pos, avoid)
        if direction:
            return direction, target_id

    # Tidak ada diamond valid ditemukan
    return None

# Memberikan langkah acak 
def random_move(pos: Position, avoid: set) -> Optional[Tuple[str, int]]:
    # Membuat dictionary arah dan posisi baru berdasarkan posisi saat ini
    directions = {
        "NORTH": Position(pos.x, pos.y - 1),
        "SOUTH": Position(pos.x, pos.y + 1),
        "WEST": Position(pos.x - 1, pos.y),
        "EAST": Position(pos.x + 1, pos.y),
    }

    # Menyaring hanya arah yang tidak menuju ke posisi yang ingin dihindari
    valid_moves = [
        direction for direction, new_pos in directions.items()
        if new_pos not in avoid
    ]

    # Jika ada gerakan yang valid, pilih satu secara acak dan kembalikan dengan nilai -2
    if valid_moves:
        return random.choice(valid_moves), -2

    # Jika tidak ada gerakan yang valid, kembalikan None
    return None

# Menghitung dan mengembalikan jarak Manhattan antara dua posisi
def manhattan_distance(p1: Position, p2: Position) -> int:
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)

# Mengembalikan True jika kedua posisi memiliki koordinat x dan y yang sama
def positions_equal(p1: Position, p2: Position) -> bool:
    return p1.x == p2.x and p1.y == p2.y

# Fungsi untuk menentukan langkah ke tujuan
def direction_towards(start: Position, goal: Position, avoid: Optional[set] = None) -> str:
    # Hitung selisih koordinat antara posisi tujuan dan posisi awal
    dx = goal.x - start.x
    dy = goal.y - start.y

    # Jika 'avoid' tidak diberikan, gunakan set kosong
    avoid = avoid or set()

    # Daftar kandidat arah jika semua arah utama diblokir
    candidates = []

    # Tentukan arah utama berdasarkan mana yang lebih dominan: horizontal (dx) atau vertikal (dy)
    if abs(dx) >= abs(dy):
        # Prioritaskan ke arah horizontal (EAST/WEST) terlebih dahulu
        if dx > 0 and not is_blocked(start.x + 1, start.y, avoid):
            return "EAST"
        elif dx < 0 and not is_blocked(start.x - 1, start.y, avoid):
            return "WEST"
        
        # Jika tidak bisa ke horizontal, coba ke vertikal (SOUTH/NORTH)
        if dy > 0 and not is_blocked(start.x, start.y + 1, avoid):
            return "SOUTH"
        elif dy < 0 and not is_blocked(start.x, start.y - 1, avoid):
            return "NORTH"
    else:
        # Prioritaskan ke arah vertikal (SOUTH/NORTH) terlebih dahulu
        if dy > 0 and not is_blocked(start.x, start.y + 1, avoid):
            return "SOUTH"
        elif dy < 0 and not is_blocked(start.x, start.y - 1, avoid):
            return "NORTH"
        
        # Jika tidak bisa ke vertikal, coba ke horizontal (EAST/WEST)
        if dx > 0 and not is_blocked(start.x + 1, start.y, avoid):
            return "EAST"
        elif dx < 0 and not is_blocked(start.x - 1, start.y, avoid):
            return "WEST"

    # Semua arah utama diblokir, buat daftar semua arah alternatif
    directions = {
        "EAST": Position(start.x + 1, start.y),
        "WEST": Position(start.x - 1, start.y),
        "SOUTH": Position(start.x, start.y + 1),
        "NORTH": Position(start.x, start.y - 1),
    }

    # Tambahkan arah yang tidak ada di posisi yang dihindari ke dalam kandidat
    for direction, pos in directions.items():
        if pos not in avoid:
            candidates.append(direction)

    # Jika semua arah terblokir, tetap tambahkan semua arah sebagai kandidat (meski berisiko)
    if not candidates:
        candidates = list(directions.keys())

    # Pilih dan kembalikan satu arah secara acak dari kandidat yang tersedia
    return random.choice(candidates)

# Fungsi untuk mengecek apakah posisi tersebut termasuk dalam set 'avoid'
def is_blocked(x: int, y: int, avoid: set) -> bool:
    return Position(x=x, y=y) in avoid