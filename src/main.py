import json
import time
import random
import argparse
import re
import requests
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union
from requests import Response
from dacite import from_dict
from colorama import Fore, Style

@dataclass
class Bot:
    name: str
    email: str
    id: str

@dataclass(frozen=True)
class Position:
    y: int
    x: int

@dataclass(frozen=True)
class Base(Position):
    pass

@dataclass
class Properties:
    points: Optional[int] = None
    pair_id: Optional[str] = None
    diamonds: Optional[int] = None
    score: Optional[int] = None
    name: Optional[str] = None
    inventory_size: Optional[int] = None
    can_tackle: Optional[bool] = None
    milliseconds_left: Optional[int] = None
    time_joined: Optional[str] = None
    base: Optional[Base] = None

@dataclass
class GameObject:
    id: int
    position: Position
    type: str
    properties: Optional[Properties] = None

@dataclass
class Config:
    generation_ratio: Optional[float] = None
    min_ratio_for_generation: Optional[float] = None
    red_ratio: Optional[float] = None
    seconds: Optional[int] = None
    pairs: Optional[int] = None
    inventory_size: Optional[int] = None
    can_tackle: Optional[bool] = None

@dataclass
class Feature:
    name: str
    config: Optional[Config] = None

@dataclass
class Board:
    id: int
    width: int
    height: int
    features: List[Feature]
    minimum_delay_between_moves: int
    game_objects: Optional[List[GameObject]]

    @property
    def bots(self) -> List[GameObject]:
        return [d for d in self.game_objects if d.type == "BotGameObject"]

    @property
    def diamonds(self) -> List[GameObject]:
        return [d for d in self.game_objects if d.type == "DiamondGameObject"]

    def get_bot(self, bot: Bot) -> Optional[GameObject]:
        for b in self.bots:
            if b.properties.name == bot.name:
                return b
        return None

    def is_valid_move(
        self, current_position: Position, delta_x: int, delta_y: int
    ) -> bool:
        if not (-1 <= delta_x <= 1) or not (-1 <= delta_y <= 1):
            print("[INVALID MOVE] Delta values must be between -1 and 1 inclusive.")
            return False

        if delta_x == delta_y:
            print("[INVALID MOVE] Delta_x and delta_y cannot be equal.")
            return False

        if not (0 <= current_position.x + delta_x < self.width):
            print("[INVALID MOVE] X-coordinate out of bounds.")
            return False

        if not (0 <= current_position.y + delta_y < self.height):
            print("[INVALID MOVE] Y-coordinate out of bounds.")
            return False

        return True

# Fungsi _unpack digunakan untuk mengakses item pada dict
def _unpack(data):
    if isinstance(data, dict):
        return data.items()
    return data

# Fungsi _snake_case mengubah string CamelCase ke snake_case
def _snake_case(value):
    first_underscore = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", first_underscore).lower()

# Fungsi _keys_to_snake_case mengubah semua key dalam dict menjadi snake_case
def _keys_to_snake_case(content):
    return {_snake_case(key): value for key, value in content.items()}

# Fungsi decode_keys melakukan konversi key ke snake_case secara rekursif
def decode_keys(data):
    formatted = {}

    # Iterasi semua item dari data
    for key, value in _unpack(_keys_to_snake_case(data)):
        if isinstance(value, dict):
            # Jika value adalah dict, lakukan decode rekursif
            formatted[key] = decode_keys(value)
        elif isinstance(value, list) and len(value) > 0:
            # Jika value adalah list, decode tiap elemen di dalamnya
            formatted[key] = []
            for _, val in enumerate(value):
                formatted[key].append(decode_keys(val))
        else:
            # Jika bukan dict atau list, simpan langsung
            formatted[key] = value

    return formatted

# Fungsi utama yang dipanggil untuk decoding API
def decode(data):
    if isinstance(data, dict):
        return decode_keys(data)

    formatted = []
    for item in data:
        formatted.append(decode_keys(item))
    return formatted

# Kelas untuk abstraksi API
@dataclass
class Api:
    url: str  # Base URL dari server API

    # Menggabungkan base URL dengan endpoint
    def _get_url(self, endpoint: str) -> str:
        return "{}{}".format(self.url, endpoint)

    # Fungsi generik untuk membuat request HTTP
    def _req(self, endpoint: str, method: str, body: dict) -> Response:
        # Log permintaan
        print(
            ">>> {} {} {}".format(
                Style.BRIGHT + method.upper() + Style.RESET_ALL,
                Fore.GREEN + endpoint + Style.RESET_ALL,
                body,
            )
        )

        # Ambil fungsi HTTP yang sesuai (get, post, dll)
        func = getattr(requests, method)
        headers = {"Content-Type": "application/json"}

        # Kirim request ke server
        res = func(self._get_url(endpoint), headers=headers, data=json.dumps(body))

        # Log responsenya
        if res.status_code == 200:
            print("<<< {} OK".format(res.status_code))
        else:
            print("<<< {} {}".format(res.status_code, res.text))

        return res

    # Ambil informasi bot dari token
    def bots_get(self, bot_token: str) -> Optional[Bot]:
        response = self._req("/bots/{}".format(bot_token), "get", {})
        data, status = self._return_response_and_status(response)
        if status == 200:
            return from_dict(Bot, data)
        return None

    # Mendaftarkan bot baru
    def bots_register(self, name: str, email: str, password: str, team: str) -> Optional[Bot]:
        response = self._req(
            "/bots",
            "post",
            {"email": email, "name": name, "password": password, "team": team},
        )
        resp, status = self._return_response_and_status(response)
        if status == 200:
            return from_dict(Bot, resp)
        return None

    # Mengambil list board yang tersedia
    def boards_list(self) -> Optional[List[Board]]:
        response = self._req("/boards", "get", {})
        resp, status = self._return_response_and_status(response)
        if status == 200:
            return [from_dict(Board, board) for board in resp]
        return None

    # Bot bergabung ke board tertentu
    def bots_join(self, bot_token: str, board_id: int) -> bool:
        response = self._req(
            f"/bots/{bot_token}/join", "post", {"preferredBoardId": board_id}
        )
        resp, status = self._return_response_and_status(response)
        return status == 200

    # Mengambil informasi detail dari sebuah board
    def boards_get(self, board_id: str) -> Optional[Board]:
        response = self._req("/boards/{}".format(board_id), "get", {})
        resp, status = self._return_response_and_status(response)
        if status == 200:
            return from_dict(Board, resp)
        return None

    # Mengirim perintah gerakan ke server dan mendapatkan board state terbaru
    def bots_move(self, bot_token: str, direction: str) -> Optional[Board]:
        response = self._req(
            "/bots/{}/move".format(bot_token),
            "post",
            {"direction": direction},
        )
        resp, status = self._return_response_and_status(response)
        if status == 200:
            return from_dict(Board, resp)
        return None

    # Recover bot berdasarkan email dan password (jika sudah terdaftar)
    def bots_recover(self, email: str, password: str) -> Optional[str]:
        try:
            response = self._req(
                "/bots/recover", "post", {"email": email, "password": password}
            )
            resp, status = self._return_response_and_status(response)
            if status == 201:  
                return resp["id"]
            return None
        except:
            return None

    # Ekstrak isi response dan kode status
    def _return_response_and_status(self, response: Response) -> Tuple[Union[dict, List], int]:

        # Parsing JSON dari server
        resp = response.json()  

        # Ambil field 'data' jika tersedia
        response_data = resp.get("data") if isinstance(resp, dict) else resp
        if not response_data:
            response_data = resp
        return decode(response_data), response.status_code

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

if __name__ == "__main__":
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