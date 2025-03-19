import logging
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from album.models import Album, Track as AlbumTrack, Review
from .forms import ReviewForm

# 로그 설정
logger = logging.getLogger(__name__)

# Spotify API 토큰 가져오기
def get_spotify_token():
    auth_url = "https://accounts.spotify.com/api/token"
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'client_secret': settings.SPOTIFY_CLIENT_SECRET,
    }

    response = requests.post(auth_url, data=auth_data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        logger.error(f"🚨 Spotify 토큰 발급 실패: {response.text}")
        return None


# Spotify API로 앨범 정보 가져오기
def get_album_from_spotify(album_id):
    token = get_spotify_token()
    if not token:
        logger.error("🚨 Spotify 토큰이 유효하지 않습니다.")
        return None

    headers = {
        'Authorization': f'Bearer {token}',
    }

    url = f'https://api.spotify.com/v1/albums/{album_id}'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"🚨 Spotify API 호출 실패: {response.status_code} - {response.text}")
        return None


# 앨범 정보 가져오기
def album_detail(request, album_id):
    album = Album.objects.filter(spotify_id=album_id).first()

    # 앨범이 DB에 없을 경우 Spotify API에서 가져오기
    if not album:
        data = get_album_from_spotify(album_id)
        if not data:
            return render(request, '404.html')

        # 앨범 저장
        album = Album.objects.create(
            spotify_id=album_id,
            name=data['name'],
            artist=", ".join([artist['name'] for artist in data['artists']]),
            image_url=data['images'][0]['url']
        )
        logger.info(f"✅ 앨범 저장 완료: {album.name}")

    # 트랙이 없는 경우 Spotify API로부터 다시 가져오기
    if not album.tracks.exists():
        data = get_album_from_spotify(album_id)
        if data:
            for item in data.get('tracks', {}).get('items', []):
                if not AlbumTrack.objects.filter(spotify_id=item['id']).exists():
                    try:
                        track = AlbumTrack.objects.create(
                            album=album,
                            spotify_id=item['id'],
                            title=item['name'],
                            duration=item['duration_ms'] // 1000
                        )
                        logger.info(f"🟣 Track 저장 완료: {track.title}")
                    except Exception as e:
                        logger.error(f"🚨 트랙 저장 실패: {e}")

    # 앨범 리뷰 가져오기
    reviews = Review.objects.filter(album=album).order_by('-created_at')

    # 리뷰 작성 로직
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('/login/')
        
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.album = album
            review.user = request.user
            review.save()
            logger.info(f"✅ 리뷰 저장 완료: {review.content}")
            return redirect('album_detail', album_id=album_id)
        else:
            logger.error(f"🚨 리뷰 저장 실패: {form.errors}")
    else:
        form = ReviewForm()

    return render(request, 'album/album_info.html', {
        'album': album,
        'tracks': album.tracks.all(),
        'reviews': reviews,
        'form': form,
    })
