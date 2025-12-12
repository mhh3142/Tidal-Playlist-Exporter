import json
import time

import requests

from tpex.exceptions import (
    TidalAuthError,
    TidalJSONDecodeError,
    TidalHTTPError,
    TidalRateLimitError,
    TidalResponseFormatError,
    TpexError
)
from tpex.TokenManager import TokenManager

class ApiClient:
    """"""
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.base_url = "https://openapi.tidal.com/v2"
        self.auth_url = "https://auth.tidal.com/v1/oauth2/token"
        self.country_code = "GB"

    def __make_request(self, url: str) -> dict:
        """
        Handles Tidal API requests, transforms json into python objects, raises custom
        excpetions and triggers reaunthentication and backoff logic. 
    
        :param url: URL of desired endpoint.
        :type url: str
        :return: Returns a dictionary containing the API response.
        :rtype: dict
        """
        time.sleep(self.token_manager.wait_time)

        try:
            json_response = requests.get(url=url, headers=self.token_manager.headers)
            json_response.raise_for_status()
            response = json.loads(json_response.content)

            return response
        except requests.exceptions.HTTPError as reqerr:
            
            if reqerr.response.status_code == 401:
                self.token_manager.fresh_token()
                raise TidalAuthError(wait_time=self.token_manager.wait_time, expired=True, message="") # Need to figure out how to get message for Tidal
            elif reqerr.response.status_code == 429: # Backoff
                self.token_manager.back_off()
                time.sleep(self.token_manager.wait_time)
                raise TidalRateLimitError()
            else:
                raise TidalHTTPError(status_code=reqerr.response.status_code)
        except json.decoder.JSONDecodeError:
            raise TidalJSONDecodeError()
        except:
            raise TpexError()
        
    def __get_all_ids(self, ids_page: dict) -> list[str]:
        """
        Paginates through a tidal ID request and returns unpacked list of all ID's.
    
        :param ids_page: Page of IDs to begin burrowing from.
        :type ids_page: dict
        :return: List of all IDs from all pages.
        :rtype: list[str]
        """
        ids = [id_dict["id"] for id_dict in ids_page["data"]]

        if "next" in ids_page["links"].keys():
            try:
                next_page = self.__make_request(url={self.token_manager.credentials.base_url}+ids_page["links"]["next"])
                ids.extend(self.__get_all_ids(ids_page=next_page))
            except:
                pass

        return ids
    
    def __get_related_ids(self, context: str, relationships_page: dict, link_tups: list[tuple[str, bool]]) -> dict:
        """
        Helper function takes context of current request and preference for related information,
        requests the related information from the Tidal API, packages it and returns a dictionary.\n

        For example if during an album request we also want a list of IDs for all release artists, context="albums",
        and link_tups contains the tuple ("artists", True).

        :param context: String indicating type of current API request
        :type context: str
        :param page: Page of current API response formatted as a dictionary.
        :type page: dict
        :param link_tups: List of tuples containing name of optional request and bool indictating whether the request should be made.
        :type link_tups: tuple
        :return: Dictionary containing all requested information.
        :rtype: dict
        """
        extras_dict = {}

        return_links = [tup[0] for tup in link_tups if tup[1]]
        for link in return_links:
            link_data = self.__make_request(url=self.token_manager.credentials.base_url+relationships_page["links"]["self"])
            extras_dict[context + link.capitalize() + "Id"] = self.__get_all_ids(ids_page=link_data)

        return extras_dict
    
    def get_artist_details(
            self,
            artist_id: str,
            return_attributes: bool=True,
            return_albums: bool=False,
            return_roles: bool=False,
            return_tracks: bool=False
    ) -> dict:
        """
        Returns a dictionary of data from an artist request along with any related
        information that has been requested.

        :param artist_id: Tidal Artist ID.
        :type artist_id: str
        :param return_attributes:
        :type return_attributes: bool
        :param return_albums:
        :type return_albums: bool
        :param return_roles:
        :type return_roles: bool
        :param return_tracks:
        :type return_tracks: bool
        :return: Dictionary containing all requested artist information.
        :rtype: dict
        """
        # As seen on the documentation, getting an artists tracks requires collapseBy query.
        artist_response = self.__make_request(url=f"{self.base_url}/artists/{artist_id}?countryCode={self.country_code}&collapseBy=FINGERPRINT")

        artist = {}
        if return_attributes:
            try:
                artist["artistId"] = artist_id
                artist["artistTitle"] = artist_response["data"]["attributes"]["name"]
            except KeyError as key_err:
                raise TidalResponseFormatError(message=str(key_err))
            
        try:
            relationships = artist_response["data"]["relationships"]
        except KeyError as key_err:
            raise TidalResponseFormatError(message=str(key_err))

        link_tups = [("albums", return_albums), ("roles", return_roles), ("tracks", return_tracks)]
        link_ids_dict = self.__get_related_ids(context="artist", relationships_page=relationships, link_tups=link_tups)

        return artist | link_ids_dict

    def get_album_details(
            self,
            album_id: str,
            return_attributes: bool=True,
            return_artists: bool=False,
            return_genres: bool=False,
            return_cover: bool=False,
            return_tracks: bool=False
    ) -> dict:
        """
        Returns a dictionary of data from an album request along with any related information
        that has been requested.

        :param album_id: Tidal Album ID.
        :type album_id: str
        :param return_attributes:
        :type return_attributes: bool
        :param return_artists:
        :type return_artists: bool
        :param return_genres:
        :type return_genres: bool
        :param return_cover:
        :type return_cover: bool
        :param return_tracks:
        :type return_tracks: bool
        :return: Dictionary containing all requested album information.
        :rtype: dict
        """
        album_response = self.__make_request(url=f"{self.base_url}/albums/{album_id}?countryCode={self.country_code}&collapseBy=FINGERPRINT")
        
        album = {}
        if return_attributes:
            try:
                album["albumId"] = album_id
                album["albumTitle"] = album_response["data"]["attributes"]["title"]
                album["albumUpc"] = album_response["data"]["attributes"]["barcodeId"]
                album["albumNumberOfVolumes"] = album_response["data"]["attributes"]["numberOfVolumes"]
                album["albumNumberOfItems"] = album_response["data"]["attributes"]["numberOfItems"]
                album["albumReleaseDate"] = album_response["data"]["attributes"]["releaseDate"]
                album["albumLabel"] = album_response["data"]["attributes"]["copyright"]["text"]
                album["albumType"] = album_response["data"]["attributes"]["type"]
            except KeyError as key_err:
                raise TidalResponseFormatError(message=str(key_err))
        
        try:
            relationships = album_response["data"]["relationships"]
        except KeyError as key_err:
            raise TidalResponseFormatError(message=str(key_err))

        link_tups = [("artists", return_artists), ("genres", return_genres), ("coverArt", return_cover), ("items", return_tracks)]
        link_ids_dict = self.__get_related_ids(context="album", relationships_page=relationships, link_tups=link_tups)

        return album | link_ids_dict

    def get_track_details(
            self,
            track_id: str,
            return_attributes: bool=True,
            return_albums: bool=False,
            return_genres: bool=False,
            return_artists: bool=False
    ) -> dict:
        """
        Returns a dictionary of data from an track request along with any related information
        that has been requested.

        :param track_id: Tidal Track ID.
        :type track_id: str
        :param return_attributes:
        :type return_attributes: bool
        :param return_albums:
        :type return_albums: bool
        :param return_genres:
        :type return_genres: bool
        :param return_artists:
        :type return_artists: bool
        :return: Dictionary containing all requested track information.
        :rtype: dict
        """
        track_response = self.__make_request(url=f"{self.base_url}/tracks/{track_id}?countryCode={self.country_code}")
        
        track = {}
        if return_attributes:

            try:
                track["trackId"] = track_id
                track["trackTitle"] = track_response["data"]["attributes"]["title"]
                track["trackVersion"] = track_response["data"]["attributes"]["version"]
                track["trackIsrc"] = track_response["data"]["attributes"]["isrc"]
                track["trackLabel"] = track_response["data"]["attributes"]["copyright"]["text"]
                track["trackDuration"] = track_response["data"]["attributes"]["duration"]
            except KeyError as key_err:
                raise TidalResponseFormatError(message=str(key_err))
            
        try:
            relationships = track_response["data"]["relationships"]
        except KeyError as key_err:
            raise TidalResponseFormatError(message=str(key_err))

        link_tups = [("albums", return_albums), ("genres", return_genres), ("artists", return_artists)]
        link_ids_dict = self.__get_related_ids(context="track", relationships_page=relationships, link_tups=link_tups)

        return track | link_ids_dict

    def get_playlist_details(
            self,
            playlist_id: str,
            return_attributes: bool=True,
            return_cover: bool=False,
            return_items: bool=False
    ) -> dict:
        """
        Returns a dictionary of data from an playlist request along with any related
        information that has been requested.

        :param playlist_id: Tidal Playlist ID.
        :type playlist_id: str
        :param return_attributes:
        :type return_attributes: bool
        :param return_cover:
        :type return_cover: bool
        :param return_items:
        :type return_items: bool
        :return: Dictionary containing all requested playlist information.
        :rtype: bool
        """
        playlist_response = self.__make_request(url=f"{self.base_url}/playlists/{playlist_id}?countryCode={self.country_code}")
        
        playlist = {}
        if return_attributes:
            try:
                playlist["playlistId"] = playlist_id
                playlist["playlistName"] = playlist_response["data"]["attributes"]["name"]
                playlist["numberOfItems"] = playlist_response["data"]["attributes"]["numberOfItems"]
            except KeyError as key_err:
                raise TidalResponseFormatError(message=str(key_err))

        try:
            relationships=playlist_response["data"]["relationships"]
        except KeyError as key_err:
            raise TidalResponseFormatError(message=str(key_err))
        
        link_tups = [("coverArt", return_cover), ("items", return_items)]
        link_ids_dict = self.__get_related_ids(context="playlist", relationships_page=relationships, link_tups=link_tups)

        return playlist | link_ids_dict