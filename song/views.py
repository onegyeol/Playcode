from django.shortcuts import render
from album.models import Album
from spotify.views import get_song_info, search_song_on_genius, get_lyrics_from_genius
from song.models import Song

def song_detail(request, song_id):  
    try:
        print(f"🔹 song_detail() 호출됨 - song_id: {song_id}")

        # DB에서 먼저 곡 정보 찾기
        song = Song.objects.filter(track_id=song_id).first()
        
        if not song:
            print(f"🔹 DB에 {song_id} 정보 없음 → Spotify API 호출")
            song_data = get_song_info(song_id, request)

            if not song_data:
                print("🚨 Spotify에서 곡 정보를 가져오지 못함")
                return render(request, "404.html", status=404)

            # Album 생성
            album_name = song_data.get("album")
            album_id = song_data.get("album_id")
            
            # 필수 필드 체크
            if album_id and album_name:
                album_instance, created = Album.objects.get_or_create(
                    spotify_id=album_id,
                    defaults={
                        "name": album_name,
                        "artist": song_data.get("artist", ""),
                        "image_url": song_data.get("image", "")
                    }
                )
                print(f"✅ {'새 앨범 생성' if created else '기존 앨범 사용'}: {album_instance.name}")
            else:
                album_instance = None
                print("🚨 album_id 또는 album_name이 누락되었습니다.")

            # Genius API에서 가사 가져오기
            genius_data = search_song_on_genius(song_data["title"], song_data["artist"])
            lyrics = get_lyrics_from_genius(genius_data["url"]) if genius_data else None

            # 곡 정보 DB에 저장
            song = Song.objects.create(
                track_id=song_id,
                title=song_data["title"],
                artist=song_data["artist"],
                album=album_instance,
                cover_url=song_data.get("image", ""),
                lyrics=lyrics,
                preview_url=song_data.get("preview_url", "")
            )

            print(f"✅ 새 곡 정보 저장 완료: {song.title} - {song.artist}")

        return render(request, "song/song_info.html", {"song": song})

    except Exception as e:
        print(f"🚨 song_detail() 오류 발생: {e}")
        return render(request, "500.html", {"error": str(e)}, status=500)
