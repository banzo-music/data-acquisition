import pytest
from unittest.mock import Mock

from acquisition.track import Track
from acquisition.artist import Artist
from acquisition.network import Network


response = {
    "tracks": [
        {
            "name": "Diddy Bop",
            "id": "000",
            "album": {
                "name": "Telefone",
                "album_type": "album"
            },
            "artists": [
                {
                    "id": "0001",
                    "name": "Noname"
                },
                {
                    "id": "0002",
                    "name": "Cam O'bi"
                },
                {
                    "id": "0003",
                    "name": "Raury"
                }
            ]
        },
        {
            "name": "Yesterday",
            "id": "111",
            "album": {
                "name": "Telefone",
                "album_type": "album"
            },
            "artists": [
                {
                    "id": "0001",
                    "name": "Noname"
                }
            ]
        },
        {
            "name": "Forever",
            "id": "222",
            "album": {
                "name": "Telefone",
                "album_type": "album"
            },
            "artists": [
                {
                    "id": "0001",
                    "name": "Noname"
                },
                {
                    "id": "2222",
                    "name": "Joseph Chilliams"
                },
                {
                    "id": "2223",
                    "name": "Ravyn Lenae"
                }
            ]
        }
    ]
}

tracks = [
    (
        Track(track_id="000", name="Diddy Bop", album="Telefone", album_type="album"),
        [
            Artist(artist_id="0001", name="Noname"),
            Artist(artist_id="0002", name="Cam O'bi"),
            Artist(artist_id="0003", name="Raury")
        ]
    ),
    (
        Track(track_id="111", name="Yesterday", album="Telefone", album_type="album"),
        [Artist(artist_id="0001", name="Noname")]
    ),
    (
        Track(track_id="222", name="Forever", album="Telefone", album_type="album"),
        [
            Artist(artist_id="0001", name="Noname"),
            Artist(artist_id="2222", name="Joseph Chilliams"),
            Artist(artist_id="2223", name="Ravyn Lenae")
        ]
    )
]


class TestNetworkTopTracks:
    def test_top_tracks(self):
        mock_spotify = Mock()
        mock_spotify.artist_top_tracks.return_value = response

        network = Network(audio_features=["a", "b"], max_tracks=10, spotify=mock_spotify)

        actual = network.top_tracks(Artist(artist_id="0001", name="Noname"))
        assert tracks == actual

    def test_top_tracks_sad(self):
        mock_spotify = Mock()
        mock_spotify.artist_top_tracks.side_effect = Exception("spotify machine broke")

        network = Network(audio_features=["a", "b"], max_tracks=10, spotify=mock_spotify)

        assert [] == network.top_tracks(Artist(artist_id="0001", name="Noname"))
        mock_spotify.artist_top_tracks.assert_called_once_with("0001")
