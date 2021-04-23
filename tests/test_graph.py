from pandas import DataFrame

from acquisition.graph import Graph
from acquisition.track import Track
from acquisition.artist import Artist

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


class TestGraph:
    def test_put_track(self):
        graph = Graph()
        track, artists = tracks[0]
        nodes = ["000", "0001", "0002", "0003"]         # track ID and all artist IDs
        edges = [("000", "0001"), ("000", "0002"), ("000", "0003")]     # track has edge to each artist

        # graph contains no nodes or edges
        assert [] == list(graph.nodes)
        assert [] == list(graph.edges)

        # put track; graph contains correct nodes and edges
        graph.put_track(track, artists)
        assert sorted(nodes) == sorted(list(graph.nodes))
        assert sorted(edges) == sorted(list(graph.edges))

        # put same track; graph contains same nodes and edges
        graph.put_track(track, artists)
        assert sorted(nodes) == sorted(list(graph.nodes))
        assert sorted(edges) == sorted(list(graph.edges))

    def test_to_dataframe(self):
        expected = DataFrame({
            "id": ["000", "111", "222", "0001", "0002", "0003", "2222", "2223"],
            "name": ["Diddy Bop", "Yesterday", "Forever", "Noname", "Cam O'bi", "Raury", "Joseph Chilliams", "Ravyn Lenae"],
            "album": ["Telefone", "Telefone", "Telefone", None, None, None, None, None],
            "album_type": ["album", "album", "album", None, None, None, None, None],
        })



# 	# TODO: test this
# 	def to_dataframe(self) -> (pd.DataFrame, pd.DataFrame):
# 		tracks = [track.__dict__ for track in self.get_node_attributes('track').values()]
# 		artists = [artist.__dict__ for artist in self.get_node_attributes('artist').values()]
# 		vertices = pd.json_normalize(tracks + artists)
# 		edges = nx.to_pandas_edgelist(self.nx_graph)
# 		return vertices, edges
#
# 	# TODO: test this
# 	def unseen_artists(self, artists: List[Artist]) -> List[Artist]:
# 		unique_artists = list(set(artists))
# 		seen_artists = self.get_node_attributes('seen')
# 		return [artist for artist in unique_artists if artist.id not in seen_artists]