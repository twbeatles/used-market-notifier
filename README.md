# 🥕 중고거래 알리미 (Used Market Notifier) v2.0

당근마켓, 번개장터, 중고나라에서 원하는 상품을 자동으로 모니터링하고 알림을 받을 수 있는 데스크톱 애플리케이션입니다.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![Playwright](https://img.shields.io/badge/Playwright-1.40+-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ 주요 기능

### 🔍 스마트 모니터링
- **다중 플랫폼 동시 검색** - 당근마켓, 번개장터, 중고나라 병렬 스크래핑
- **키워드 기반 필터링** - 원하는 상품만 알림
- **가격 범위 설정** - 최소/최대 가격 필터
- **제외 키워드** - 불필요한 상품 자동 필터링

### 🛡️ 고급 봇 탐지 우회 (v2.0)
- **15가지 Stealth 기술** - WebDriver 숨김, Chrome 객체 모방
- **WebGL/Canvas 핑거프린트 보호**
- **인간 행동 시뮬레이션** - 무작위 지연, 스크롤 패턴

### 🔍 디버깅 시스템 (v2.0)
- **자동 스크린샷** - 에러 발생 시 페이지 캡처
- **네트워크 로그** - 요청/응답 기록
- **세션 리포트** - JSON 형식 진단 데이터

### 🎨 모던 UI/UX (v2.0)
- **Glassmorphism 디자인** - 반투명 카드, 그라디언트 버튼
- **펄스 애니메이션** - 상태 표시 시각 효과
- **호버 리프트 효과** - 카드 상호작용 피드백
- **Catppuccin 테마** - 눈이 편안한 다크 모드

### 📱 다중 알림
- **Telegram** - 이미지 포함 알림 지원
- **Discord** - Webhook 연동
- **Slack** - Webhook 연동

### 📊 통계 및 분석
- **대시보드** - 플랫폼별/키워드별 통계
- **가격 추이** - 관심 상품 가격 변동 추적
- **즐겨찾기** - 관심 상품 저장

---

## 📦 설치

### 요구사항
- Python 3.10 이상
- Windows 10/11

### 패키지 설치
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 🚀 실행

```bash
# GUI 모드 (기본)
python main.py

# CLI 모드 (백그라운드)
python main.py --cli

# 디버그 모드
python main.py --debug
```

---

## ⚙️ 설정

### 키워드 추가
1. "🔍 키워드" 탭 → "+ 새 키워드" 클릭
2. 검색어, 가격 범위, 플랫폼 선택
3. 저장

### Telegram 알림 설정
1. [@BotFather](https://t.me/BotFather)에서 봇 생성 → 토큰 복사
2. [@userinfobot](https://t.me/userinfobot)에서 Chat ID 확인
3. 설정 → Telegram 탭에서 입력

---

## 📁 프로젝트 구조

```
used_market_notifier/
├── main.py                  # 진입점
├── monitor_engine.py        # 모니터링 핵심 로직
├── settings_manager.py      # 설정 관리
├── db.py                    # SQLite 데이터베이스
├── models.py                # 데이터 모델
├── scrapers/
│   ├── playwright_base.py   # Playwright 베이스 (Stealth 통합)
│   ├── stealth.py           # 봇 탐지 우회 모듈
│   ├── debug.py             # 디버깅 도구
│   ├── danggeun.py
│   ├── bunjang.py
│   └── joonggonara.py
├── notifiers/
│   ├── telegram_notifier.py
│   ├── discord_notifier.py
│   └── slack_notifier.py
└── gui/
    ├── main_window.py       # 메인 윈도우
    ├── styles.py            # Glassmorphism 스타일
    ├── components.py        # 커스텀 컴포넌트
    ├── keyword_manager.py   # 키워드 관리
    └── stats_widget.py      # 통계 위젯
```

---

## 🔧 빌드

```bash
pyinstaller used_market_notifier.spec
```

결과: `dist/중고거래알리미.exe` (약 50-60MB)

> ⚠️ Playwright 브라우저는 별도 설치 필요: `playwright install chromium`

---

## 🆕 v2.0 변경사항

| 항목 | v1.x | v2.0 |
|------|------|------|
| 스크래핑 | Selenium (순차) | Playwright (병렬) |
| 봇 탐지 우회 | 기본 UA | 15가지 Stealth 기술 |
| 디버깅 | 없음 | 스크린샷/네트워크 로그 |
| UI 디자인 | 기본 | Glassmorphism + 애니메이션 |
| 성능 | ~5초 시작 | ~2초 시작 |

---

## 📝 라이선스

MIT License
