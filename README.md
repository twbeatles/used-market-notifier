# 🛒 중고거래 알리미 (Used Market Notifier)

실시간 중고거래 플랫폼 모니터링 및 알림 프로그램

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ 주요 기능

### 🔍 검색 및 모니터링
- **다중 플랫폼**: 당근마켓, 번개장터, 중고나라
- **키워드 모니터링**: 무제한 등록, 개별 설정
- **가격 필터**: 최소/최대 가격 범위
- **제외 키워드**: 원하지 않는 매물 필터링
- **지역 필터**: 당근마켓 지역 검색

### 📢 알림
| 플랫폼 | 설정 |
|--------|------|
| 텔레그램 | 봇 토큰 + 채팅 ID |
| 디스코드 | 웹훅 URL |
| 슬랙 | 웹훅 URL |

### 📊 데이터 관리
- 즐겨찾기 / 가격 추적
- 판매 상태 필터 (판매중/예약중/판매완료)
- CSV/Excel 내보내기
- 자동 백업/복원

### 🎨 UI/UX
- Catppuccin Mocha 다크 테마
- 글래스모피즘 카드 효과
- 단축키: F5 새로고침, Ctrl+S 시작/정지

---

## 🚀 실행 방법

### 실행 파일 (권장)
```
dist/UsedMarketNotifier.exe
```

### Python 개발 실행
```bash
pip install -r requirements.txt
python main.py
```

---

## 📁 프로젝트 구조

```
used_market_notifier/
├── main.py              # 진입점
├── monitor_engine.py    # 모니터링 엔진
├── db.py                # 데이터베이스
├── settings_manager.py  # 설정 관리
├── models.py            # 데이터 모델
├── constants.py         # 상수 정의
├── gui/                 # UI 컴포넌트
│   ├── main_window.py
│   ├── styles.py
│   ├── components.py
│   └── ...
├── scrapers/            # 플랫폼 스크래퍼
│   ├── danggeun.py
│   ├── bunjang.py
│   └── joonggonara.py
└── notifiers/           # 알림 모듈
    ├── telegram.py
    ├── discord.py
    └── slack.py
```

---

## ⚙️ 설정

### 알림 설정
1. **텔레그램**: @BotFather에서 봇 생성 → 토큰/채팅ID 입력
2. **디스코드**: 서버 설정 → 연동 → 웹훅 URL 복사
3. **슬랙**: 앱 설정 → Incoming Webhooks 활성화

---

## 📝 최근 업데이트 (2026-01)

- ✅ 크롤링 아키텍처 재설계 (안정성 향상)
- ✅ UI/UX 개선 (테이블 가독성, 토스트 알림)
- ✅ 성능 최적화 (DB 인덱스, 드라이버 관리)
- ✅ 메시지박스 버튼 가시성 수정
- ✅ 스레드 종료 시 앱 안정성 개선

---

## 📄 라이선스

MIT License
