from playlist_exporter.api_client import get_access_token
from playlist_exporter.api_client import get_playlist_data

from playlist_exporter.exporter import export_to_excel

from playlist_exporter.formatter import playlist_frame_formatter

from dotenv import load_dotenv
import os

"""
    Loads our private information into the program, creates our important api variables, calls the api module to get api information, calls the format module to format the
    information, then finally calls the exporter module to export the information.
"""
def main(playlist_id: str="0dc0fa56-98d0-4c96-9931-72dfa47d2d01") -> None:

    load_dotenv
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    base_url = "https://openapi.tidal.com/v2"
    headers = {
        "Authorization": "Bearer " + get_access_token(client_id=client_id, client_secret=client_secret)
    }
    country_code = "GB" # UK country code

    playlist_dict_raw = get_playlist_data(base_url=base_url, headers=headers, country_code=country_code, playlist_id=playlist_id)
    playlist_frame = playlist_frame_formatter(playlist_raw=playlist_dict_raw)

    export_to_excel(playlist_frame=playlist_frame)

main()