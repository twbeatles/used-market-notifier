# 🥕 중고거래 알리미 (Used Market Notifier)

당근마켓, 번개장터, 중고나라에서 원하는 상품을 자동으로 모니터링하고 알림을 받을 수 있는 데스크톱 애플리케이션입니다.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 주요 기능

- **🔍 키워드 모니터링** - 원하는 검색어로 여러 플랫폼 동시 검색
- **💰 가격 필터** - 최소/최대 가격 설정으로 원하는 가격대만 알림
- **🚫 제외 키워드** - 불필요한 상품 필터링
- **📱 다중 알림** - Telegram, Discord, Slack 지원
- **📊 통계 대시보드** - 검색 결과 시각화
- **⭐ 즐겨찾기** - 관심 상품 저장
- **⚡ 성능 최적화** - 단일 브라우저 공유로 메모리 절약 (60%↓)
- **💾 데이터 지속성** - 재시작 시 이전 알림 및 통계 즉시 복원
- **📋 전체 매물 조회** - 검색/필터링으로 모든 매물 확인
- **🛡️ 스마트 필터링** - 판매완료/예약중/광고 자동 제외 (정확도 향상)

## 🖥️ 스크린샷

| 키워드 관리 | 통계 대시보드 |
|------------|-------------|
| 카드 기반 UI로 키워드 관리 | 플랫폼별 분포 및 일별 추이 차트 |

## 📦 설치

### 요구사항
- Python 3.10 이상
- Chrome 브라우저 (스크래핑용)

### 패키지 설치
```bash
pip install -r requirements.txt
```

### 필수 패키지
```
PyQt6>=6.4.0
selenium>=4.10.0
webdriver-manager>=4.0.0
aiohttp>=3.8.0
matplotlib>=3.7.0
openpyxl>=3.1.0
```

## 🚀 실행

### GUI 모드
```bash
python main.py
```

### CLI 모드
```bash
python main.py --cli
```

## ⚙️ 설정

### 키워드 추가
1. 프로그램 실행
2. "🔍 키워드" 탭에서 "+ 새 키워드" 클릭
3. 검색어, 가격 범위, 플랫폼 선택
4. 저장

### 알림 설정
1. "⚙️ 설정" 버튼 클릭
2. Telegram/Discord/Slack 탭에서 활성화
3. 토큰 및 채널 ID 입력

#### Telegram 봇 설정
1. @BotFather에서 새 봇 생성
2. 토큰 복사
3. @userinfobot에서 chat_id 확인

## 📁 프로젝트 구조

```
used_market_notifier/
├── main.py              # 진입점
├── monitor_engine.py    # 모니터링 핵심 로직
├── db.py                # SQLite 데이터베이스
├── settings_manager.py  # 설정 관리
├── models.py            # 데이터 모델
├── scrapers/            # 플랫폼별 스크래퍼
│   ├── danggeun.py
│   ├── bunjang.py
│   └── joonggonara.py
├── notifiers/           # 알림 채널
│   ├── telegram_notifier.py
│   ├── discord_notifier.py
│   └── slack_notifier.py
└── gui/                 # PyQt6 GUI
    ├── main_window.py
    ├── keyword_manager.py
    ├── stats_widget.py
    └── ...
```

## 🔧 빌드

### PyInstaller로 실행파일 생성
```bash
pyinstaller used_market_notifier.spec
```

## ⚠️ 알려진 제한사항

- **중고나라**: Headless 모드에서 네이버 봇 감지로 인해 검색 결과가 제한될 수 있습니다.
- **당근마켓**: 지역 필터는 URL 기반이 아닌 검색 결과에서 필터링됩니다.

## 📝 라이선스

MIT License
