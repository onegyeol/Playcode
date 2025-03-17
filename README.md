# Playcode
Playcode는 Spotify API와 Genius API를 연동하여 음악을 추천하고, 곡 정보와 가사를 제공하는 뮤직 추천 웹 서비스입니다. 사용자는 Spotify에서 원하는 노래를 검색하고, 해당 곡의 정보와 가사를 확인할 수 있습니다.

## ⚙️ 주요 기능

#### 1. Spotify API 연동
- 사용자는 Spotify의 트랙 ID로 노래 정보를 가져올 수 있습니다.
- 곡명, 아티스트, 앨범, 앨범 커버 이미지, 미리듣기 링크 제공.

#### 2. Genius API 연동
- 가져온 노래 정보를 기반으로 Genius API를 통해 가사 제공.
- 크롤링을 통해 사용자에게 전 곡 가사 제공
  
#### 3. 데이터베이스 관리
- Django ORM을 사용하여 Spotify 및 Genius API 데이터를 MySQL 데이터베이스에 저장.
- 중복된 데이터는 업데이트하고, 없는 데이터는 새로 추가.
  
#### 4. 웹 UI
- Django Template을 기반으로 한 사용자 친화적인 UI 제공.


## 💻 기술 스택
- Backend: Python, Django, FastAPI
- Frontend: HTML, CSS, Django Template
- Database: MySQL (Docker로 컨테이너 관리)
- API: Spotify API, Genius API
- Deployment: AWS EC2, Docker

  
