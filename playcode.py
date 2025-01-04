from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

client_id = '73f20fc707ae4dab81206b43ee55727a'
client_secret = '94916665f35842a88d17c00588a944d0'

sp = Spotify(auth_manager=SpotifyOAuth(client_id,
                                       client_secret,
                                       redirect_uri='http://localhost:8080/callback'))
result = sp.search('IU', limit=1, type='artist')
print(result)

uri = 'spotify:artist:3HqSLMAZ3g3d5poNaI7GOU' # 형태 : spotify:artist:(아티스트 id)
artist = sp.artist(uri)
print(artist)