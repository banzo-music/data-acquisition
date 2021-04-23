from typing import Dict, Any, List

import networkx as nx
import pandas as pd

from acquisition.artist import Artist
from acquisition.track import Track


class Graph:
	def __init__(self, nx_graph: nx.Graph = None):
		self.nx_graph = nx.Graph()
		if nx_graph:
			self.nx_graph = nx_graph
		self.nodes = self.nx_graph.nodes
		self.edges = self.nx_graph.edges

	def add_node(self, n, **attr):
		self.nx_graph.add_node(n, **attr)

	def add_edge(self, a, b, **attr):
		self.nx_graph.add_edge(a, b, **attr)

	def get_node_attributes(self, attr_name: str) -> Dict[str, Any]:
		return nx.get_node_attributes(self.nx_graph, attr_name)

	# TODO: test this
	def to_dataframe(self) -> (pd.DataFrame, pd.DataFrame):
		tracks = [track.__dict__ for track in self.get_node_attributes('track').values()]
		artists = [artist.__dict__ for artist in self.get_node_attributes('artist').values()]
		vertices = pd.json_normalize(tracks + artists)
		edges = nx.to_pandas_edgelist(self.nx_graph)
		return vertices, edges

	# TODO: test this
	def unseen_artists(self, artists: List[Artist]) -> List[Artist]:
		unique_artists = list(set(artists))
		seen_artists = self.get_node_attributes('seen')
		return [artist for artist in unique_artists if artist.id not in seen_artists]

	def put_track(self, track: Track, artists: List[Artist]):
		if track.id in self.nodes:
			return

		self.add_node(track.id, track=track)
		for artist in artists:
			seen = artist.attr.get('seen')
			if seen:
				self.add_node(artist.id, artist=artist, seen=seen)
			else:
				self.add_node(artist.id, artist=artist)
			self.add_edge(track.id, artist.id)
