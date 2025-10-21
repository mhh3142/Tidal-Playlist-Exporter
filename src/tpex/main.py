import os

from dotenv import load_dotenv

from tpex.api_client import get_base_and_headers
from tpex.api_client import get_playlist_data

from tpex.exporter import export_to_excel

from tpex.formatter import playlist_frame_formatter

"""
    I REPLACED THE get_artist_token FUNCTION WITH A get_base_and_headers FUNCTION. I CHANGED main TO MATCH THIS. MAKE SURE YOU MENTION THIS IN COMMIT DETAILS
"""

"""
    Loads our private information into the program, creates our important api variables, calls the api module to get api information, calls the format module to format the
    information, then finally calls the exporter module to export the information.
"""
def main(playlist_id: str="0dc0fa56-98d0-4c96-9931-72dfa47d2d01") -> None:

    load_dotenv
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    base_url, headers = get_base_and_headers(client_id=client_id, client_secret = client_secret)
    country_code = "GB"

    playlist_dict_raw = get_playlist_data(base_url=base_url, headers=headers, country_code=country_code, playlist_id=playlist_id)
    playlist_frame = playlist_frame_formatter(playlist_raw=playlist_dict_raw)

    export_to_excel(playlist_frame=playlist_frame)

main()