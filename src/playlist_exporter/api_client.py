import requests
import json
import time

""" 
    Requests an api token using the Lime Blue private information. I should have a look to see what the whole response looks like. I may use a different authenication
    method in the future.
"""
def get_access_token(client_id: str, client_secret: str) -> str:

    url = "https://auth.tidal.com/v1/oauth2/token"
    body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(url=url, data=body)
    json_response = json.loads(response.content)
    access_token = json_response["access_token"]

    return access_token

""" The repeat code for when I make a request to the api. It's poorly done I just made this in a hurry and it needs to be improved on ASAP """
def get_request(url: str, headers: str):
    
    response = requests.get(url=url, headers=headers)
    time.sleep(0.3)
    json_response = json.loads(response.content)
    
    return json_response

""" 
    Tidal has a return limit for information, when the amount of information exceeds this limit tidal returns the max amount it can and then provides a next link with the location
    of the remainder of the data. This function burrows into the deepest "next" it can find, stores the data in a list and then unwinds. It then recursively returns the data from
    each page and appends the "deeper" data.
    
    Nervous about having recursion here as I'm always told it's risky
"""
def get_all_ids(base_url: str, headers: str, json: str) -> list[str]:

    ids = [id_dict["id"] for id_dict in json["data"]]

    if "next" in json["links"].keys():
        next_page = get_request(url=base_url+json["links"]["next"], headers=headers)
        ids.extend(get_all_ids(base_url=base_url, headers=headers, json=next_page))
    
    return ids

""" 
    This is a multi purpose function. Tidal often returns locations of request related information rather than the data itself. Any request that has related information can call 
    this function and it will return specified bits of related information.
"""
def get_link_ids(base_url: str, headers: str, self: str, json: str, link_tups: tuple) -> dict:

    self_dict = {}

    return_links = [tup[0] for tup in link_tups if tup[1]]
    if len(return_links):
        for link in return_links:
            link_data = get_request(url=base_url+json[link]["links"]["self"], headers=headers)
            self_dict[self + link.capitalize() + "Id"] = get_all_ids(base_url=base_url, headers=headers, json=link_data)

    return self_dict

""" Returns a dictionary of data from an artist request along with any related information that has been requested """
def get_artist_details(base_url: str, headers: str, country_code: str, artist_id: str, return_attributes: bool=True, return_albums: bool=False, return_roles: bool=False, return_tracks: bool=False) -> dict:
    
    # As seen on the documentation, getting an artists tracks requires collapseBy query.
    json_artist = get_request(url=f"{base_url}/artists/{artist_id}?countryCode={country_code}&collapseBy=FINGERPRINT", headers=headers)

    artist = {}
    if return_attributes:
        artist["artistId"] = artist_id
        artist["artistTitle"] = json_artist["data"]["attributes"]["name"]

    link_tups = (("albums", return_albums), ("roles", return_roles), ("tracks", return_tracks))
    link_ids_dict = get_link_ids(base_url=base_url, headers=headers, self="artist", json=json_artist["data"]["relationships"], link_tups=link_tups)
    
    return artist | link_ids_dict

""" Returns a dictionary of data from an album request along with any related information that has been requested """
def get_album_details(base_url: str, headers: str, country_code: str, album_id: str, return_attributes: bool=True, return_artists: bool=False, return_genres: bool=False, return_cover: bool=False, return_tracks: bool=False) -> dict:

    json_album = get_request(url=f"{base_url}/albums/{album_id}?countryCode={country_code}&collapseBy=FINGERPRINT", headers=headers)

    album = {}
    if return_attributes:
        album_attributes = json_album["data"]["attributes"]
        album["albumId"] = album_id
        album["albumTitle"] = album_attributes["title"]
        album["albumUpc"] = album_attributes["barcodeId"]
        album["albumNumberOfVolumes"] = album_attributes["numberOfVolumes"]
        album["albumNumberOfItems"] = album_attributes["numberOfItems"] # I just added this line
        album["albumReleaseDate"] = album_attributes["releaseDate"]
        album["albumLabel"] = album_attributes["copyright"]["text"]
        album["albumType"] = album_attributes["type"]

    link_tups = (("artists", return_artists), ("genres", return_genres), ("coverArt", return_cover), ("items", return_tracks))
    link_ids_dict = get_link_ids(base_url=base_url, headers=headers, self="album", json=json_album["data"]["relationships"], link_tups=link_tups)

    return album | link_ids_dict

""" Returns a dictionary of data from an track request along with any related information that has been requested """
def get_track_details(base_url: str, headers: str, country_code: str, track_id: str, return_attributes: bool=True, return_albums: bool=False, return_genres: bool=False, return_artists: bool=False) -> dict:

    json_track = get_request(url=f"{base_url}/tracks/{track_id}?countryCode={country_code}", headers=headers) # No collapse by because tracks tend not to have more than 20 albums, genres and artists
    
    track = {}
    if return_attributes:
        track_attributes = json_track["data"]["attributes"]
        track["trackId"] = track_id
        track["trackTitle"] = track_attributes["title"]
        track["trackVersion"] = track_attributes["version"]
        track["trackIsrc"] = track_attributes["isrc"]
        track["trackLabel"] = track_attributes["copyright"]["text"]
        track["trackDuration"] = track_attributes["duration"]

    link_tups = (("albums", return_albums), ("genres", return_genres), ("artists", return_artists))
    link_ids_dict = get_link_ids(base_url=base_url, headers=headers, self="track", json=json_track["data"]["relationships"], link_tups=link_tups)

    return track | link_ids_dict

""" Returns a dictionary of data from an playlist request along with any related information that has been requested """
def get_playlist_details(base_url: str, headers: str, country_code: str, playlist_id: str, return_attributes: bool=True, return_cover: bool=False, return_items: bool=False) -> dict:

    json_playlist = get_request(url=f"{base_url}/playlists/{playlist_id}?countryCode={country_code}", headers=headers) # I think I need collapseBy=FINGERPRINT
    
    playlist = {}
    if return_attributes:
        playlist_attributes = json_playlist["data"]["attributes"]
        playlist["playlistId"] = playlist_id
        playlist["playlistName"] = playlist_attributes["name"]
        playlist["numberOfItems"] = playlist_attributes["numberOfItems"]

    link_tups = (("coverArt", return_cover), ("items", return_items))
    link_ids_dict = get_link_ids(base_url=base_url, headers=headers, self="playlist", json=json_playlist["data"]["relationships"], link_tups=link_tups)

    return playlist | link_ids_dict

""" This function has to use dynamic programming to help with the tidal's request throttling. """
def get_playlist_data(base_url: str, headers: str, country_code: str, playlist_id: str) -> list[dict]:

    playlist = []
    
    sparse_playlist = get_playlist_details(base_url=base_url, headers=headers, country_code=country_code, playlist_id=playlist_id, return_items=True)

    albums = {}
    artists = {}

    for item_id in sparse_playlist["playlistItemId"]:
        
        track_dict = {}
        track = get_track_details(base_url=base_url, headers=headers, country_code=country_code, track_id=item_id, return_albums=True, return_artists=True)

        for artist_id in track["trackArtistsId"]: # This adds the featured artists
            if artist_id not in artists.keys():
                artists[artist_id] = get_artist_details(base_url=base_url, headers=headers, country_code=country_code, artist_id=artist_id)["artistTitle"]

        for album_id in track["trackAlbumsId"]:
            if album_id not in albums.keys():
                albums[album_id] = get_album_details(base_url=base_url, headers=headers, country_code=country_code, album_id=album_id, return_artists=True)

                for artist_id in albums[album_id]["albumArtistsId"]: # This adds the release artists
                    if artist_id not in artists.keys():
                        artists[artist_id] = get_artist_details(base_url=base_url, headers=headers, country_code=country_code, artist_id=artist_id)["artistTitle"]

        # Now we store all the track information into a nice and full dictionary
        track_dict["albumArtist"] = [artists[artist_id] for artist_id in albums[track["trackAlbumsId"][0]]["albumArtistsId"]]
        
        track_dict["trackArtists"] = [artists[artist_id] for artist_id in track["trackArtistsId"]]
        track_dict["trackTitle"] = track["trackTitle"]
        track_dict["trackVersion"] = track["trackVersion"]
        track_dict["trackDuration"] = track["trackDuration"]
        track_dict["trackIsrc"] = track["trackIsrc"]
        track_dict["trackPublishing"] = track["trackLabel"]

        # might be worth a variable main_album_dict = albums[track["trackAlbumsId"][0]]
        track_dict["albumArtists"] = [artists[artist_id] for artist_id in albums[track["trackAlbumsId"][0]]["albumArtistsId"]]
        track_dict["albumTitle"] = albums[track["trackAlbumsId"][0]]["albumTitle"]
        track_dict["albumType"] = albums[track["trackAlbumsId"][0]]["albumType"]
        track_dict["albumUpc"] = albums[track["trackAlbumsId"][0]]["albumUpc"]
        track_dict["albumReleaseDate"] = albums[track["trackAlbumsId"][0]]["albumReleaseDate"]
        track_dict["albumCopy"] = albums[track["trackAlbumsId"][0]]["albumLabel"]

        playlist.append(track_dict)

    return playlist