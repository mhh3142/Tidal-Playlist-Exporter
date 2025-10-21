import re

import pandas as pd

""" Uses regex to convert the date from Tidal's YYYY-MM-DD format into Lime Blue's DD/MM/YY format """
def format_date(date: str) -> str: # Just format the date how Limeblue likes it

    split_list = re.split(pattern=r"-{1}", string=date)
    split_list.reverse()

    return "/".join(split_list)

""" Uses regex to convert the time from Tidal's ISO 8601 format into Lime Blues hh:mm:ss format. It automatically ignores time values over 24 hrs """
def format_time(time: str) -> str:

    pattern1 = r"T(\d{1,2}[HMS]){1,3}$" # This regex isn't super air tight and relies on the second regex to catch some of the bad formats it will let through e.g 30S10S2S
    practical_time = re.search(pattern=pattern1, string=time)

    if practical_time is not None:
        
        pattern2 = r"T(?:(\d{1,2})H)?(?:(\d{1,2})M)?(?:(\d{1,2})S)?"
        match = re.search(pattern=pattern2, string=practical_time.group())

        nums = [("0" * (2 - len(num))) + num if num else "00" for num in match.groups()]

        return ":".join(nums)
    else:
        return time

""" Takes our raw playlist list and only selects the information we want to show with names that agree with the Lime Blue naming style then converts it to a dataframe ready to be
    exported to excel. """
def playlist_frame_formatter(playlist_raw: list[dict]) -> pd.DataFrame:

    playlist_clean = []

    for track_dict in playlist_raw:
        
        track_dict_clean = {}

        track_dict_clean["Release Artist"] = ", ".join(artist_name for artist_name in track_dict["albumArtists"])
        track_dict_clean["Track Band / Artist Name"] = ", ".join(artist_name for artist_name in track_dict["trackArtists"])
        track_dict_clean["Recording Title"] = track_dict["trackTitle"]
        # track_dict_clean["Subtitle / Version / Mixname"]
        track_dict_clean["ISRC"] = track_dict["trackIsrc"]
        track_dict_clean["Album Title"] = track_dict["albumTitle"]
        track_dict_clean["Catalogue Number"] = track_dict["albumUpc"]
        track_dict_clean["Original Release Label"] = "" # ask mario which one he wants I've forgotten
        track_dict_clean["Duration (hh:mm:ss)"] = format_time(track_dict["trackDuration"])
        track_dict_clean["Release Date (DD/MM/YYYY)"] = format_date(track_dict["albumReleaseDate"])
        # track_dict_clean["Album Type"]
        # track_dict_clean["Publishing"]
        # track_dict_clean["Copy"]
        track_dict_clean["Source"] = "Tidal"

        playlist_clean.append(track_dict_clean)

    return playlist_clean
