import spotipy
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

from album.models import Album
from .models import Playlist, Track
from spotify.views import refresh_token

def display_playlists(request):
    """
    - 사용자가 /playlist/로 접근하면 Spotify 인증 여부 확인
    - 인증되지 않았다면 /spotify/login/으로 리다이렉트
    - 인증이 완료된 후 자동으로 Spotify에서 데이터를 가져오고 화면에 출력
    """
    token_info = request.session.get("spotify_token")

    # 인증 여부 확인
    if not token_info:
        print("Spotify 인증 필요 → 자동 로그인 진행")
        return redirect("spotify_login")

    # 토큰이 만료된 경우에만 자동 갱신
    sp = spotipy.Spotify(auth=token_info["access_token"])
    try:
        sp.current_user()  # API 호출 → 유효성 검사
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:  # 토큰 만료됨
            print("Access Token 만료 → 자동 갱신 진행")
            token_info = refresh_token(request)
            if not token_info:
                print("토큰 갱신 실패 → 로그인 필요")
                return redirect("spotify_login")
            sp = spotipy.Spotify(auth=token_info["access_token"])  # 새로운 토큰으로 Spotipy 재인증

    # Spotify에서 플레이리스트 가져와서 DB 저장
    fetch_playlists(request)

    # 저장된 플레이리스트 가져와서 HTML 렌더링
    playlists = Playlist.objects.all()
    return render(request, "playlist/playlist.html", {"playlists": playlists})

# 만약 위의 display_playlist()가 오류가 난다면
"""
def display_playlists(request):
    
    token_info = request.session.get("spotify_token")

    # token_info가 JSON 문자열일 경우 변환
    if isinstance(token_info, str):
        try:
            token_info = json.loads(token_info)
        except json.JSONDecodeError:
            print("🚨 JSON 파싱 실패: token_info가 유효한 JSON이 아님")
            return redirect("spotify_login")

    # token_info가 dict가 아닐 경우 에러 방지
    if not isinstance(token_info, dict) or "access_token" not in token_info:
        print("🚨 token_info가 올바르지 않음:", token_info)
        return redirect("spotify_login")

    # Spotify 인증 확인 (만료된 경우 자동 갱신)
    sp = spotipy.Spotify(auth=token_info["access_token"])
    try:
        sp.current_user()
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:
            print("🔹 Access Token 만료 → 자동 갱신 진행")
            token_info = refresh_token(request)
            if not token_info:
                print("🚨 토큰 갱신 실패 → 로그인 필요")
                return redirect("spotify_login")
            sp = spotipy.Spotify(auth=token_info["access_token"])

    # Spotify에서 플레이리스트 가져와서 DB 저장
    fetch_playlists(request)

    # 저장된 플레이리스트 가져와서 HTML 렌더링
    playlists = Playlist.objects.all()
    return render(request, "playlist/playlist.html", {"playlists": playlists})
"""

# Spotify API에서 플레이리스트 가져오기 & MySQL에 저장
def fetch_playlists(request):
    token_info = request.session.get("spotify_token")

    if not token_info:
        return JsonResponse({"error": "Spotify 인증이 필요합니다."}, status=401)

    sp = spotipy.Spotify(auth=token_info["access_token"])

    try:
        playlists = sp.current_user_playlists()
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:  # 토큰 만료 시 갱신 후 재시도
            print("Access Token 만료 → 자동 갱신 진행")
            token_info = refresh_token(request)
            if not token_info:
                return JsonResponse({"error": "토큰 갱신 실패, 다시 로그인하세요."}, status=401)
            sp = spotipy.Spotify(auth=token_info["access_token"])
            playlists = sp.current_user_playlists()
        else:
            return JsonResponse({"error": str(e)}, status=e.http_status)

    # 플레이리스트 데이터 저장*
    for playlist in playlists["items"]:
        Playlist.objects.update_or_create(
            spotify_id=playlist["id"],
            defaults={
                "name": playlist["name"],
                "owner": playlist["owner"]["display_name"],
                "track_count": playlist["tracks"]["total"],
                "image_url": playlist["images"][0]["url"] if playlist["images"] else None
            }
        )

    return JsonResponse({"message": "Playlists fetched and saved successfully."})


# JSON API로 플레이리스트 데이터 제공 (AJAX 비동기 로드용)
def get_playlists_json(request):
    playlists = Playlist.objects.all().values("name", "image_url")
    return JsonResponse(list(playlists), safe=False)


# 플레이리스트의 곡 목록 가져오기
def get_playlist_tracks(request, playlist_id):
    """
    - Spotify에서 해당 플레이리스트의 곡 목록을 가져옴
    - 이미 저장된 경우 DB에서 불러옴
    """
    token_info = request.session.get("spotify_token")
    if not token_info:
        return redirect("spotify_login")

    # 플레이리스트 객체 가져오기
    playlist = get_object_or_404(Playlist, spotify_id=playlist_id)

    # Spotify API 객체 생성
    sp = spotipy.Spotify(auth=token_info["access_token"])

    # DB에 곡 목록이 없으면 Spotify API 호출
    if not Track.objects.filter(playlist=playlist).exists():
        try:
            results = sp.playlist_tracks(playlist_id)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 401:  # 토큰 만료 시 자동 갱신 후 재시도
                print("🔹 Access Token 만료 → 자동 갱신 진행")
                token_info = refresh_token(request)
                if not token_info:
                    return redirect("spotify_login")
                sp = spotipy.Spotify(auth=token_info["access_token"])
                results = sp.playlist_tracks(playlist_id)
            else:
                return JsonResponse({"error": str(e)}, status=e.http_status)

        # DB에 저장
        for item in results["items"]:
            track = item["track"]
            album_data = track["album"]
            album_spotify_id = album_data["id"]

            album, created = Album.objects.get_or_create(
                spotify_id=album_spotify_id,
                defaults={
                    "name": album_data["name"],
                    "artist": ", ".join([artist["name"] for artist in album_data["artists"]]),
                    "image_url": album_data["images"][0]["url"] if album_data["images"] else None
                }
            )

            if created:
                print(f"✅ 새 앨범 생성: {album.name}", flush=True)

            Track.objects.update_or_create(
                spotify_id=track["id"],
                playlist=playlist,
                defaults={
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                    "album": album  
                }
            )

    tracks_without_album = Track.objects.filter(playlist=playlist, album__isnull=True)
    for track in tracks_without_album:
        track_data = sp.track(track.spotify_id)
        album_data = track_data["album"]
        album_spotify_id = album_data["id"]

        # 앨범 객체 가져오기 또는 생성
        album, created = Album.objects.get_or_create(
            spotify_id=album_spotify_id,
            defaults={
                "name": album_data["name"],
                "artist": ", ".join([artist["name"] for artist in album_data["artists"]]),
                "image_url": album_data["images"][0]["url"] if album_data["images"] else None
            }
        )

        # 트랙의 album 필드 업데이트
        track.album = album
        track.save()
        print(f"✅ 기존 트랙 '{track.name}'에 앨범 '{album.name}' 연결 완료", flush=True)

    # 저장된 곡 목록 가져오기
    tracks = Track.objects.filter(playlist=playlist)

    # 각 트랙의 album과 album.spotify_id 로그 출력
    for track in tracks:
        if track.album:
            print(f"✅ Track: {track.name}, Album ID: {track.album.spotify_id}", flush=True)
        else:
            print(f"❌ Track: {track.name} has no Album linked!", flush=True)

    return render(request, "playlist/playlist_tracks.html", {"playlist": playlist, "tracks": tracks})
