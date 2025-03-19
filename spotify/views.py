import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import JsonResponse
from playlist.models import Playlist
from song.models import Song
from .models import SpotifyToken  # 토큰 저장 모델
import requests  
from bs4 import BeautifulSoup

SPOTIFY_API_URL = "https://api.spotify.com/v1/"
GENIUS_API_KEY = settings.GENIUS_API_KEY
GENIUS_API_URL = "https://api.genius.com"

# Spotify 로그인 (OAuth 인증)
def spotify_login(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="playlist-read-private playlist-read-collaborative user-read-private"
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Callback 처리 및 액세스 토큰 저장
def spotify_callback(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,  
        client_secret=settings.SPOTIFY_CLIENT_SECRET,  
        redirect_uri=settings.SPOTIFY_REDIRECT_URI, 
        scope="user-library-read playlist-read-private"
    )

    code = request.GET.get("code")
    if not code:
        print("🚨 Spotify Callback: code가 없음")
        return redirect("/spotify/login/")  

    try:
        token_info = sp_oauth.get_access_token(code=code, as_dict=True)
        if not token_info:
            print("🚨 토큰 정보가 None입니다!")
            return redirect("/spotify/login/")

        print(f"✅ 토큰 저장 완료: {token_info}")
        request.session["spotify_token"] = token_info
        return redirect("/playlist/")  
    except Exception as e:
        print(f"🚨 Spotify Callback 오류 발생: {e}")
        return redirect("/spotify/login/")

def refresh_token(request):
    """
    Spotify 액세스 토큰 갱신 (토큰이 없으면 None 반환)
    """
    token_info = request.session.get("spotify_token")
    
    if not token_info or "refresh_token" not in token_info:
        print("🚨 리프레시 토큰 없음 → 세션 초기화 후 로그인 필요")
        request.session.pop("spotify_token", None)  
        return None  # ✅ 변경: API 호출 시 오류 방지를 위해 None 반환

    refresh_token = token_info["refresh_token"]

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code == 200:
        new_token_info = response.json()
        print(f"✅ 새 토큰 발급 완료: {new_token_info}")

        token_info["access_token"] = new_token_info["access_token"]
        if "refresh_token" in new_token_info:
            token_info["refresh_token"] = new_token_info["refresh_token"]

        request.session["spotify_token"] = token_info  
        return token_info  # ✅ 변경: 새 토큰 반환
    else:
        print(f"🚨 Spotify API 토큰 갱신 실패: {response.status_code}, 응답: {response.text}")
        request.session.pop("spotify_token", None)  
        return None  # ✅ 변경: API 호출 시 오류 방지를 위해 None 반환

# 현재 로그인한 사용자 정보 가져오기
def get_user_profile(request):
    token_info = request.session.get("spotify_token")
    if not token_info or "access_token" not in token_info:
        print("🚨 사용자 세션에 토큰 없음 → 로그인 필요")
        return redirect("/spotify/login/")

    access_token = token_info["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return JsonResponse({
            "display_name": user_data.get("display_name"),
            "id": user_data.get("id"),
            "email": user_data.get("email", "N/A"),
            "image": user_data["images"][0]["url"] if user_data.get("images") else None
        })
    elif response.status_code == 401:
        print("🚨 액세스 토큰 만료 → 리프레시 토큰 요청")
        token_info = refresh_token(request)
        if token_info:
            return get_user_profile(request)
        else:
            return redirect("/spotify/login/")
    else:
        print(f"🚨 Spotify API 호출 오류: {response.status_code} - {response.text}")
        return JsonResponse({"error": "Spotify API 호출 실패"}, status=500)

# 🏆 Spotify API에서 특정 곡 정보 가져오기 + 가사 추가
def get_song_info(song_id, request):
    token_info = request.session.get("spotify_token")

    if not token_info or "access_token" not in token_info:
        token_info = refresh_token(request)
        if not token_info:
            return None

    access_token = token_info["access_token"]
    url = f"{SPOTIFY_API_URL}tracks/{song_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()

        # 기본 곡 정보 가져오기
        song_info = {
            "track_id": song_id,
            "title": data["name"],
            "artist": data["artists"][0]["name"],
            "album": data["album"]["name"],
            "image": data["album"]["images"][0]["url"],
            "preview_url": data.get("preview_url", None)
        }

        # 🎵 추가: 가사 가져오기
        song_info["lyrics"] = get_song_lyrics(song_info["title"], song_info["artist"])

        return song_info
    elif response.status_code == 401:
        token_info=refresh_token(request)
        if token_info:
            return get_song_info(song_id, request)
        return None
    
    return None

# 🎤 Musixmatch API로 가사 가져오기
def get_song_lyrics(song_title, artist_name):
    """
    Musixmatch API를 사용하여 특정 곡의 가사를 가져오는 함수
    """
    url = "https://api.musixmatch.com/ws/1.1/matcher.lyrics.get"
    params = {
        "q_track": song_title,  # 곡 제목
        "q_artist": artist_name,  # 가수명
        "apikey": settings.MUSIXMATCH_API_KEY,  # Django settings에서 API 키 가져오기
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        lyrics_data = data["message"]["body"].get("lyrics", {})

        if not lyrics_data:
            return "가사를 찾을 수 없습니다."

        lyrics = lyrics_data.get("lyrics_body", "가사를 찾을 수 없습니다.")

        # 🔹 **불필요한 텍스트 제거 (Musixmatch는 가사 일부만 제공)**
        lyrics = lyrics.replace("******* This Lyrics is NOT for Commercial use *******", "").strip()
        
        return lyrics
    return f"Musixmatch API 오류 발생 (HTTP {response.status_code})"

# 🎧 노래 제목으로 곡 정보 가져오기 (검색)
def get_spotify_song_details(song_name, request):
    token_info = request.session.get("spotify_token")
    if not token_info or "access_token" not in token_info:
        return None
    
    access_token = token_info["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{SPOTIFY_API_URL}search", headers=headers, params={
        "q": song_name,
        "type": "track",
        "limit": 1
    })
    
    if response.status_code == 200:
        data = response.json()
        if data["tracks"]["items"]:
            track = data["tracks"]["items"][0]
            return {
                "title": track["name"],
                "artist": track["artists"][0]["name"],
                "album": track["album"]["name"],
                "cover_url": track["album"]["images"][0]["url"]
            }
    return None

def search_song_on_genius(title, artist):
    """
    Genius API를 사용하여 특정 곡의 정보를 검색 (정확한 아티스트 매칭 추가)
    """
    headers = {"Authorization": f"Bearer {GENIUS_API_KEY}"}
    search_url = f"{GENIUS_API_URL}/search"
    params = {"q": f"{title} {artist}"}

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"🚨 Genius API 호출 실패: {response.status_code}")
        return None

    json_data = response.json()
    
    hits = json_data.get("response", {}).get("hits", [])
    if not hits:
        print("🔹 검색 결과 없음")
        return None

    # 🔹 검색 결과에서 정확한 아티스트 매칭
    for hit in hits:
        song_data = hit["result"]
        genius_artist = song_data["primary_artist"]["name"].lower()
        input_artist = artist.lower()

        if genius_artist == input_artist:  # 정확한 아티스트 매칭
            print(f"✅ 정확한 곡 찾음: {song_data['title']} - {song_data['url']}")
            return {"url": song_data["url"]}

    print("🚨 정확한 아티스트와 일치하는 곡을 찾지 못함")
    return None  # 정확한 곡이 없으면 None 반환

def get_lyrics_from_genius(song_url):
    """
    Genius에서 가사 크롤링 (줄바꿈 보정)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://genius.com/",
    }

    response = requests.get(song_url, headers=headers)

    if response.status_code != 200:
        print(f"🚨 가사 페이지 접근 실패: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # 🔹 가사 영역 찾기
    lyrics_divs = soup.find_all("div", class_="Lyrics__Container-sc-926d9e10-1")

    if not lyrics_divs:
        print("🚨 가사 크롤링 실패: 가사 태그를 찾을 수 없음")
        return None

    # 🔹 HTML 태그 정리 및 줄바꿈 보정
    raw_lyrics = "\n".join([div.get_text(separator="\n") for div in lyrics_divs])

    # 🔹 가사 줄바꿈 패턴 보정
    cleaned_lyrics = []
    for line in raw_lyrics.split("\n"):
        line = line.strip()

        # 빈 줄 제거 (줄바꿈이 너무 많아지는 경우 방지)
        if not line:
            continue

        # 단어 하나만 분리되어 있는 경우, 이전 줄과 합침 (예: [SZA] 가 따로 있는 문제 해결)
        if len(line.split()) == 1 and cleaned_lyrics:
            cleaned_lyrics[-1] += " " + line
        else:
            cleaned_lyrics.append(line)

    # 🔹 최종 가사 문자열 생성
    lyrics = "\n".join(cleaned_lyrics)
    return lyrics



# EC2 서버로 실행 시 오류나면 아래의 코드로 진행하기
"""
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.shortcuts import redirect

# 🎵 Spotify 로그인 (OAuth 인증)
def spotify_login(request):
    token_info = request.session.get("spotify_token")

    # ✅ token_info가 없으면 새 로그인 요청
    if not token_info:
        print("🔹 세션에 저장된 token_info 없음 → 새로운 로그인 요청")
        return redirect_to_spotify_login()

    # ✅ token_info가 문자열이면 JSON 변환 시도
    if isinstance(token_info, str):
        try:
            token_info = json.loads(token_info)
        except json.JSONDecodeError:
            print("🚨 JSON 파싱 실패: token_info가 유효한 JSON이 아님")
            request.session.pop("spotify_token", None)  # 세션에서 삭제
            return redirect_to_spotify_login()

    # ✅ token_info가 dict인지 확인
    if not isinstance(token_info, dict) or "access_token" not in token_info:
        print("🚨 token_info가 올바르지 않음:", token_info)
        return redirect_to_spotify_login()

    # ✅ Spotify API 호출하여 현재 사용자 정보 확인 (토큰 검증)
    try:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        sp.current_user()  # 현재 사용자 정보 요청 → 토큰 유효성 확인
        print("✅ 유효한 토큰 확인 완료 → 플레이리스트 페이지 이동")
        return redirect("playlist")  # 정상적인 토큰이면 플레이리스트 페이지로 이동
    except spotipy.exceptions.SpotifyException as e:
        print(f"🚨 기존 토큰 만료 또는 Spotify API 오류 발생: {e}")
        request.session.pop("spotify_token", None)  # 만료된 토큰 삭제

    # ✅ 새로운 로그인 요청
    return redirect_to_spotify_login()

# ✅ Spotify 로그인 URL 생성
def redirect_to_spotify_login():
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="playlist-read-private playlist-read-collaborative user-read-private"
    )
    auth_url = sp_oauth.get_authorize_url()
    print(f"🔹 Spotify 인증 페이지로 이동: {auth_url}")
    return redirect(auth_url)

def spotify_callback(request):
    Spotify 로그인 후 access_token을 세션에 저장
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="playlist-read-private playlist-read-collaborative user-read-private"
    )

    code = request.GET.get("code")
    if not code:
        print("🚨 Spotify Callback: code가 없음")
        return redirect("spotify_login")  # 다시 로그인 시도

    try:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        request.session["spotify_token"] = token_info  # ✅ 세션 저장
        print("✅ 토큰 저장 완료:", token_info)
        return redirect("playlist")  # 로그인 후 플레이리스트 페이지로 이동
    except Exception as e:
        print(f"🚨 Spotify Callback 오류 발생: {e}")
        return redirect("spotify_login")  # 로그인 실패 시 다시 시도


# 토큰 리프레시
def refresh_token(request):
    token_info = request.session.get("spotify_token")

    # ✅ 리프레시 토큰이 없으면 세션 삭제 후 로그인으로 리다이렉트
    if not token_info or "refresh_token" not in token_info:
        print("🚨 리프레시 토큰 없음 → 세션 초기화 후 로그인 필요")
        request.session.pop("spotify_token", None)  # 세션에서 삭제
        return None  # 로그인 페이지로 리다이렉트하게 유도

    refresh_token = token_info["refresh_token"]

    # ✅ Spotify API에 refresh token을 사용한 새로운 access token 요청
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code == 200:
        try:
            new_token_info = response.json()
        except json.decoder.JSONDecodeError:
            print("🚨 Spotify API 응답 JSON 파싱 실패")
            return None

        # ✅ 새로운 access_token 업데이트
        token_info["access_token"] = new_token_info.get("access_token")

        # ✅ 새로운 refresh_token이 있으면 업데이트
        if "refresh_token" in new_token_info:
            token_info["refresh_token"] = new_token_info["refresh_token"]

        # ✅ 세션에 저장 (자동 반영됨)
        request.session["spotify_token"] = token_info
        print("✅ 액세스 토큰 갱신 완료:", token_info)
        return token_info

    else:
        print(f"🚨 Spotify API 토큰 갱신 실패: {response.status_code}, 응답: {response.text}")
        request.session.pop("spotify_token", None)  # 실패 시 세션 초기화
        return None  # 로그인 재요청 필요

# 사용자 프로필         
def get_user_profile(request):
    token_info = request.session.get("spotify_token")
    
    # ✅ 토큰이 없으면 로그인 필요
    if not token_info:
        print("🚨 사용자 세션에 토큰 없음 → 로그인 필요")
        return redirect("/spotify/login/")

    sp = spotipy.Spotify(auth=token_info.get("access_token"))
    
    try:
        user_data = sp.current_user()
        return JsonResponse({
            "display_name": user_data.get("display_name"),
            "id": user_data.get("id"),
            "email": user_data.get("email", "N/A"),
            "image": user_data["images"][0]["url"] if user_data.get("images") else None
        })
    except spotipy.exceptions.SpotifyException:
        print("🚨 Spotify API 호출 실패 → 토큰 만료 가능성")
        return redirect("/spotify/login/")

"""