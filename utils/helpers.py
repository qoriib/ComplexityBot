import re

# Fungsi _unpack digunakan untuk mengakses item pada dict
# Jika input adalah dictionary, kembalikan pasangan key-value menggunakan .items()
# Jika bukan dict (kemungkinan list), kembalikan langsung datanya
def _unpack(data):
    if isinstance(data, dict):
        return data.items()
    return data

# Fungsi _snake_case mengubah string CamelCase ke snake_case
# Contoh: "nextMoveAvailableAt" => "next_move_available_at"
def _snake_case(value):
    first_underscore = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", first_underscore).lower()

# Fungsi _keys_to_snake_case mengubah semua key dalam dict menjadi snake_case
# Tidak rekursif, hanya berlaku satu level saja
def _keys_to_snake_case(content):
    return {_snake_case(key): value for key, value in content.items()}

# Fungsi decode_keys melakukan konversi key ke snake_case secara rekursif
# Cocok untuk struktur nested dict dan list
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

# Fungsi utama yang dipanggil untuk decoding:
# - Jika input dict, panggil decode_keys langsung
# - Jika input list, panggil decode_keys pada tiap elemen list
def decode(data):
    if isinstance(data, dict):
        return decode_keys(data)

    formatted = []
    for item in data:
        formatted.append(decode_keys(item))
    return formatted