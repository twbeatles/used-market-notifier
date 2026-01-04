# 🥕 중고거래 알리미 (Used Market Notifier)

당근마켓, 번개장터, 중고나라에서 키워드를 모니터링하고 새 상품이 등록되면 실시간 알림을 보내는 프로그램입니다.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![Selenium](https://img.shields.io/badge/Scraping-Selenium-orange)

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 🔍 키워드 모니터링 | 여러 키워드 동시 모니터링 |
| 🏪 3대 플랫폼 지원 | 당근마켓, 번개장터, 중고나라 |
| 📢 알림 전송 | Telegram, Discord, Slack |
| 💰 가격 필터 | 최소/최대 가격 설정 |
| 📊 통계 대시보드 | 일별/키워드별 통계 |
| ⭐ 즐겨찾기 | 관심 매물 저장 |
| 📝 매물 메모 | 상태 태그 및 메모 추가 |
| 📊 매물 비교 | 다중 매물 비교 기능 |
| 💾 키워드 프리셋 | 필터 설정 저장/불러오기 |
| 🔔 키워드별 알림 | 개별 알림 ON/OFF |

---

## 🚀 설치 방법

### 요구사항
- Python 3.10 이상
- Chrome 브라우저 (Selenium용)

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 실행
```bash
# GUI 모드
python main.py

# CLI 모드 (백그라운드)
python main.py --cli
```

---

## 📦 빌드 (EXE)

### PyInstaller 빌드
```bash
# UPX 설치 (선택, 압축용)
# https://github.com/upx/upx/releases

# 빌드 실행
pyinstaller used_market_notifier.spec
```

빌드된 파일: `dist/UsedMarketNotifier.exe`

---

## ⌨️ 키보드 단축키

| 단축키 | 기능 |
|--------|------|
| `Ctrl+S` | 모니터링 시작/중지 |
| `Ctrl+,` | 설정 열기 |
| `Ctrl+Q` | 프로그램 종료 |
| `Ctrl+1~6` | 탭 전환 |
| `F1` | 단축키 도움말 |
| `F5` | 현재 탭 새로고침 |
| `Enter` | 매물 링크 열기 |
| `F` | 즐겨찾기 추가 |

---

## 📁 프로젝트 구조

```
used_market_notifier/
├── main.py              # 진입점
├── monitor_engine.py    # 코어 모니터링 엔진
├── db.py                # SQLite 데이터베이스
├── settings_manager.py  # 설정 관리
├── models.py            # 데이터 모델
├── scrapers/            # 스크래퍼
│   ├── selenium_base.py
│   ├── danggeun.py
│   ├── bunjang.py
│   └── joonggonara.py
├── notifiers/           # 알림 전송
│   ├── telegram_notifier.py
│   ├── discord_notifier.py
│   └── slack_notifier.py
├── gui/                 # PyQt6 GUI
│   ├── main_window.py
│   ├── keyword_manager.py
│   ├── listings_widget.py
│   └── ...
└── requirements.txt
```

---

## ⚙️ 설정

### 알림 설정 (설정 → 알림)
- **Telegram**: Bot Token + Chat ID
- **Discord**: Webhook URL
- **Slack**: Webhook URL

### 모니터링 설정
- 검색 주기 (기본: 5분)
- Headless 모드 (브라우저 숨김)
- 시스템 트레이 최소화

---

## 📄 라이선스

MIT License

---

## 🙏 기여

이슈 및 PR 환영합니다!
