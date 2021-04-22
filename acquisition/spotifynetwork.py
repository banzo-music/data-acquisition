import json
import traceback
from typing import List, Dict, Any, Tuple

import spotipy
import networkx as nx
import pandas as pd

from artist import Artist
from playlist import Playlist
from track import Track


class Network:
	def __init__(self, audio_features: List[str], max_tracks: int):
		self.spotify = spotipy.Spotify(auth_manager=spotipy.oauth2.SpotifyClientCredentials())
		self.graph = nx.Graph()
		self.audio_features = audio_features
		self.max_tracks = max_tracks

	def search_tracks(self, artist_name: str, seen: bool = False) -> List[Tuple[Track, List[Artist]]]:
		tracks = {}
		limit = 50
		offset = 0
		total = 1
		while offset <= total and offset <= self.max_tracks:
			try:
				results = self.spotify.search(artist_name, type='track', limit=limit, offset=offset)
			except Exception as e:
				print(
					f"exception while searching, skipping batch of tracks:\n",
					format_traceback(e)
				)
				offset += limit
				continue

			offset += limit
			total = results['tracks']['total']

			for result in results['tracks']['items']:
				if artist_name in [artist['name'] for artist in result['artists']]:
					tracks[result['name']] = (
						self.track_from_response(result),
						[self.artist_from_response(artist, seen) for artist in result['artists']]
					)

		return list(tracks.values())

	def top_tracks(self, artist: Artist, seen: bool = False) -> List[Tuple[Track, List[Artist]]]:
		try:
			results = self.spotify.artist_top_tracks(artist.id)
		except Exception as e:
			print(
				f"exception while getting top tracks, skipping artist ({artist.name}):\n",
				format_traceback(e)
			)
			return []

		tracks = {}
		for result in results['tracks']:
			tracks[result['name']] = (
				self.track_from_response(result),
				[self.artist_from_response(artist, seen) for artist in result['artists']]
			)

		return list(tracks.values())

	def put_track(self, track: Track, artists: List[Artist]):
		if track.id not in self.graph.nodes():
			self.graph.add_node(track.id, track=track)
			for artist in artists:
				seen = artist.attr.get('seen')
				if seen:
					self.graph.add_node(artist.id, artist=artist, seen=seen)
				else:
					self.graph.add_node(artist.id, artist=artist)
				self.graph.add_edge(track.id, artist.id)

	def related_artists(self, artist: Artist, seen: bool = False) -> List[Artist]:
		try:
			results = self.spotify.artist_related_artists(artist.id)
		except Exception as e:
			print(
				f"exception while getting related artists, skipping artist ({artist.name}):\n",
				format_traceback(e)
			)
			return []

		if results['artists']:
			return [self.artist_from_response(artist, seen) for artist in results['artists']]
		else:
			return []

	def get_audio_features(self, tracks: List[Track]):
		n = 100
		batches = [tracks[i * n:(i+1) * n] for i in range((len(tracks) + n-1) // n)]

		for batch in batches:
			tracks_map = {}
			for track in batch:
				tracks_map[track.id] = track

			try:
				results = self.spotify.audio_features(tracks_map.keys())
			except Exception as e:
				print(
					f"exception while getting audio features, skipping batch of tracks:\n",
					format_traceback(e)
				)
				continue

			if len(results) <= 0:
				continue

			for result in results:
				if result:
					track_id = result['id']
					if track_id in tracks_map:
						audio_features = {}
						for name in self.audio_features:
							audio_features[name] = result.get(name)
						tracks_map[track_id].set_attrs(audio_features)

	def get_playlist(self, playlist_id: str) -> Playlist:
		try:
			playlist = self.spotify.playlist(playlist_id=playlist_id)
		except Exception as e:
			print(
				f"exception while getting playlist, skipping playlist ({playlist_id}):\n",
				format_traceback(e)
			)
			return Playlist(playlist_id='', name='', entries=[])

		playlist_name = playlist['name']
		total_tracks = playlist['tracks']['total']

		entries = {}
		offset = 0
		limit = 50
		while offset <= total_tracks:
			try:
				results = self.spotify.playlist_tracks(playlist_id=playlist_id, offset=offset, limit=limit)
			except Exception as e:
				print(
					f"exception while getting playlist tracks, skipping batch of tracks ({playlist_id}):\n",
					format_traceback(e)
				)
				offset += limit
				continue

			offset += limit
			if len(results['items']) <= 0 or not results['items'][0]:
				break

			for result in results['items']:
				if result['track']:
					track = result['track']
					entries[track['name']] = (
						self.track_from_response(track),
						[self.artist_from_response(artist) for artist in track['artists']]
					)

		return Playlist(
			playlist_id=playlist_id,
			name=playlist_name,
			entries=list(entries.values())
		)			

	def to_dataframe(self) -> (pd.DataFrame, pd.DataFrame):
		tracks = [track.__dict__ for track in nx.get_node_attributes(self.graph, 'track').values()]
		artists = [artist.__dict__ for artist in nx.get_node_attributes(self.graph, 'artist').values()]
		vertices = pd.json_normalize(tracks + artists)
		edges = nx.to_pandas_edgelist(self.graph)
		return vertices, edges

	def from_dataframe(self, vertices: pd.DataFrame, edges: pd.DataFrame):
		graph = nx.from_pandas_edgelist(edges)
		records = vertices.to_dict('records')
		for record in records:
			attr = {}
			for k, v in record.items():
				if 'attr' in k:
					attr[k.replace("attr.", "")] = v

			if record['node_type'] == 'track':
				graph.add_node(record['id'], track=Track(
					track_id=record['id'],
					name=record['name'],
					album=record['album'],
					album_type=record['album_type'],
					attr=attr
				))
			elif record['node_type'] == 'artist':
				graph.add_node(record['id'], artist=Artist(
					artist_id=record['id'],
					name=record['name'],
					attr=attr
				))
			else:
				print("weird node found; skipping")
				continue

		self.graph = graph

	def unseen_artists(self, artists: List[Artist]) -> List[Artist]:
		unique_artists = list(set(artists))
		seen_artists = nx.get_node_attributes(self.graph, 'seen')
		return [artist for artist in unique_artists if artist.id not in seen_artists]

	def artist_from_response(self, response: Dict[str, Any], seen: bool = False) -> Artist:
		attr = {
			'popularity': response.get('popularity'),
			'genres': response.get('genres')
		}

		if seen or response['id'] in nx.get_node_attributes(self.graph, 'seen'):
			attr['seen'] = True

		artist = Artist(artist_id=response['id'], name=response['name'], attr=attr)
		return artist

	@staticmethod
	def track_from_response(response: Dict[str, Any]) -> Track:
		return Track(
			track_id=response['id'],
			name=response['name'],
			album=response['album']['name'],
			album_type=response['album']['album_type']
		)


def format_traceback(e: Exception) -> str:
	json.dumps(traceback.format_tb(e.__traceback__), indent=3)
