import json
import requests
from requests import Response
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union
from colorama import Fore, Style 
from dacite import from_dict
from utils.helpers import decode
from utils.models import Board, Bot

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