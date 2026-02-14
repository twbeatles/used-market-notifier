# 🛒 중고거래 알리미 (Used Market Notifier)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.4+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/Selenium-4.x-orange.svg" alt="Selenium">
  <img src="https://img.shields.io/badge/SQLite3-DB-blueviolet.svg" alt="SQLite3">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  <strong>당근마켓, 번개장터, 중고나라를 실시간으로 모니터링하여<br>
  원하는 상품이 올라오면 즉시 알림을 받으세요!</strong>
</p>

---

## ✨ 주요 기능

### 🔍 스마트 검색
| 기능 | 설명 |
|------|------|
| **다중 플랫폼** | 당근마켓 🥕, 번개장터 ⚡, 중고나라 🛒 동시 검색 |
| **무제한 키워드** | 원하는 만큼 키워드 등록 가능 |
| **가격 필터** | 최소/최대 가격 범위 설정 |
| **지역 필터** | 당근마켓 지역 검색 지원 |
| **제외 키워드** | 불필요한 매물 자동 필터링 |
| **키워드 그룹** | 관련 키워드 그룹화 관리 |
| **개별 설정** | 키워드별 검색 주기, 알림 토글 |

### 📢 실시간 알림

| 플랫폼 | 설정 방법 |
|--------|----------|
| **Telegram** | Bot Token + Chat ID |
| **Discord** | Webhook URL |
| **Slack** | Webhook URL |

**알림 기능:**
- ✅ 새 상품 알림
- ✅ 가격 인하 알림
- ✅ 알림 스케줄 (요일/시간 설정)
- ✅ 키워드별 알림 토글
- ✅ 테스트 알림 전송

### 📊 데이터 관리

| 기능 | 설명 |
|------|------|
| **즐겨찾기** | 관심 매물 저장, 메모 추가 |
| **가격 추적** | 가격 변동 이력 자동 기록 |
| **통계 대시보드** | 플랫폼별/일별 통계, 차트 |
| **매물 비교** | 여러 매물 나란히 비교 |
| **내보내기** | CSV, Excel 형식 지원 |
| **자동 백업** | 주기적 백업, 복원 기능 |
| **데이터 정리** | 오래된 매물 자동 삭제 |

### 🏷️ 자동 태깅 시스템

상품 제목을 분석하여 자동으로 태그를 부여합니다:

| 태그 | 트리거 키워드 | 아이콘 |
|------|--------------|--------|
| A급 | A급, 에이급, 상태좋음, 최상, S급 | ✨ |
| 풀박스 | 풀박스, 미개봉, 새제품, 미사용 | 📦 |
| 급처 | 급처, 급매, 빨리, 오늘만 | 🔥 |
| 네고가능 | 네고가능, 네고, 협의가능 | 💬 |
| 택포 | 택포, 택배포함, 무배 | 📮 |
| 직거래 | 직거래, 직거래만 | 🤝 |
| 정품 | 정품, 구매영수증, 보증서 | ✅ |

### 💬 메시지 템플릿

판매자에게 보낼 메시지를 미리 작성해두세요:

- **기본 문의** - "아직 판매중인가요?"
- **가격 문의** - "네고 가능할까요?"
- **직거래 문의** - "직거래 가능하실까요?"
- **상태 문의** - "상세한 상태가 어떻게 되나요?"
- **플랫폼 전용 템플릿** - 당근 안부인사, 번개장터 빠른문의

**사용 가능한 변수:**
- `{title}` - 상품 제목
- `{price}` - 판매 가격
- `{seller}` - 판매자 이름
- `{location}` - 지역
- `{target_price}` - 내 목표 가격

### 🎨 모던 UI

- **Catppuccin Mocha 테마**: 세련된 다크 테마
- **라이트 모드 지원**: 시스템 설정 연동
- **글래스모피즘 카드**: 반투명 효과
- **부드러운 애니메이션**: 호버, 전환 효과
- **시스템 트레이**: 백그라운드 실행
- **토스트 알림**: 인앱 알림

### ⌨️ 단축키

| 단축키 | 기능 |
|--------|------|
| `F5` | 현재 탭 새로고침 |
| `Ctrl+S` | 모니터링 시작/정지 |
| `Ctrl+,` | 설정 열기 |
| `Ctrl+N` | 새 키워드 추가 |
| `Enter` | 선택 항목 열기 |
| `Ctrl+F` | 즐겨찾기 추가 |
| `F1` | 단축키 도움말 |

---

## 🚀 시작하기

### 방법 1: 실행 파일 (권장)

1. [Releases](https://github.com/twbeatles/used-market-notifier/releases)에서 최신 버전 다운로드
2. `UsedMarketNotifier.exe` 실행
3. 키워드 추가하고 모니터링 시작!

### 방법 2: 소스 코드 실행

```bash
# 저장소 클론
git clone https://github.com/twbeatles/used-market-notifier.git
cd used-market-notifier

# 가상환경 생성 (선택)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 의존성 설치
pip install -r requirements.txt

# 브라우저 준비 (Selenium)
# - Chrome(또는 Chromium 기반 브라우저)이 설치되어 있어야 합니다.
# - 드라이버는 webdriver-manager가 자동으로 내려받습니다.

# 실행
python main.py
```

### CLI 모드 (백그라운드 실행)

```bash
python main.py --cli
```

---

## 📖 사용 방법

### 1. 키워드 등록

1. **키워드 탭**에서 `+ 키워드 추가` 버튼 클릭
2. 검색 키워드 입력 (예: "맥북 프로 M2")
3. 옵션 설정:
   - **가격 범위**: 최소/최대 가격
   - **지역**: 당근마켓 지역 필터
   - **제외 키워드**: "부품", "고장" 등
   - **플랫폼**: 검색할 플랫폼 선택
4. 저장

### 2. 알림 설정

1. **설정** (⚙️) 버튼 클릭
2. 원하는 알림 채널 탭 선택:

**Telegram 설정:**
1. [@BotFather](https://t.me/BotFather)에서 봇 생성
2. 봇 토큰 복사
3. [@userinfobot](https://t.me/userinfobot)에서 Chat ID 확인
4. 설정에 입력 후 "테스트" 버튼으로 확인

**Discord 설정:**
1. Discord 서버 설정 → 연동 → 웹훅
2. 새 웹훅 생성 → URL 복사
3. 설정에 입력 후 "테스트" 버튼으로 확인

**Slack 설정:**
1. Slack 앱 설정 → Incoming Webhooks 활성화
2. 웹훅 URL 복사
3. 설정에 입력 후 "테스트" 버튼으로 확인

### 3. 모니터링 시작

1. 헤더의 **▶ 시작** 버튼 클릭 (또는 `Ctrl+S`)
2. 상태 표시줄에서 진행 상황 확인
3. 새 상품 발견 시 자동 알림

### 4. 매물 관리

**매물 목록 탭:**
- 검색으로 매물 필터링
- 플랫폼/판매상태 필터
- 더블클릭으로 상세 페이지 열기
- 우클릭 메뉴: 즐겨찾기, 판매자 차단, 메시지 작성

**즐겨찾기 탭:**
- 관심 매물 저장
- 메모 및 목표 가격 설정
- 가격 변동 알림

**통계 탭:**
- 플랫폼별 매물 분포
- 일별 수집 통계
- 가격 변동 이력
- CSV/Excel 내보내기

---

## 📁 프로젝트 구조

```
used_market_notifier/
├── main.py              # 진입점 (GUI/CLI 모드)
├── monitor_engine.py    # 핵심 모니터링 엔진
├── db.py                # SQLite 데이터베이스
├── settings_manager.py  # 설정 관리
├── models.py            # 데이터 모델
├── constants.py         # 상수 정의
├── auto_tagger.py       # 자동 태깅
├── backup_manager.py    # 백업/복원
├── export_manager.py    # 내보내기
├── message_templates.py # 메시지 템플릿
├── gui/                 # UI 컴포넌트
│   ├── main_window.py   # 메인 윈도우
│   ├── styles.py        # 테마 스타일시트
│   ├── keyword_manager.py
│   ├── settings_dialog.py
│   ├── listings_widget.py
│   ├── favorites_widget.py
│   ├── stats_widget.py
│   └── ...
├── scrapers/            # 플랫폼 스크래퍼
│   ├── danggeun.py      # 당근마켓
│   ├── bunjang.py       # 번개장터
│   ├── joonggonara.py   # 중고나라
│   └── stealth.py       # 봇 탐지 우회
└── notifiers/           # 알림 모듈
    ├── telegram_notifier.py
    ├── discord_notifier.py
    └── slack_notifier.py
```

---

## ⚙️ 설정 파일

### settings.json

```json
{
  "check_interval_seconds": 300,
  "headless_mode": true,
  "notifications_enabled": true,
  "minimize_to_tray": true,
  "auto_start_monitoring": false,
  "theme_mode": "dark",
  "keywords": [...],
  "notifiers": [...],
  "auto_backup_enabled": true,
  "auto_backup_interval_days": 7,
  "auto_tagging_enabled": true
}
```

> 참고:
> - 리포지토리에는 `settings.example.json`만 포함됩니다. 실제 실행을 위해서는 `settings.json`을 생성해 토큰/웹훅 등을 채워주세요.
> - `settings.json`, `listings.db*`, `notifier.log`, `__pycache__/`, `backup/` 등은 로컬 런타임 데이터로서 Git에 포함되지 않도록 `.gitignore` 처리되어 있습니다.
> - 과거 레거시 설정/알림 샘플 코드는 `legacy/`에 있으며, 현재 메인 앱에서는 사용하지 않습니다.

### 데이터 파일

| 파일 | 설명 |
|------|------|
| `settings.json` | 사용자 설정 |
| `listings.db` | 매물 데이터베이스 |
| `notifier.log` | 로그 파일 |
| `backup/` | 자동 백업 폴더 |

---

## 🔧 고급 설정

### 검색 주기 조정

기본 검색 주기는 5분입니다. `설정 > 일반`에서 변경 가능합니다.

| 주기 | 권장 상황 |
|------|----------|
| 1분 | 급한 매물 모니터링 (IP 차단 위험) |
| 5분 | 일반적인 사용 (기본값) |
| 10분 | 장기 모니터링 |

### 브라우저 설정

- **Headless 모드**: 브라우저 창 숨김 (기본)
- **브라우저 표시**: 디버깅용

### 데이터 정리

`설정 > 유지보수`에서:
- 오래된 매물 자동 삭제 (기본 30일)
- 즐겨찾기/메모 있는 매물 보호
- 백업 보관 개수 설정

---

## 🐛 문제 해결

### 스크래핑이 안 될 때

1. **네트워크 확인**: 인터넷 연결 상태 확인
2. **브라우저 표시 모드**: `설정 > 일반 > 브라우저 표시` 활성화
3. **Chrome 업데이트/재설치**: 브라우저가 너무 오래됐으면 페이지가 깨질 수 있습니다
4. **로그 확인**: 앱의 `로그` 탭에서 에러 메시지 확인

### 알림이 안 올 때

1. **알림 활성화 확인**: `설정 > 일반 > 알림 활성화`
2. **채널 설정 확인**: 토큰/웹훅 URL 재확인
3. **테스트 전송**: 각 채널의 "테스트" 버튼 사용
4. **스케줄 확인**: 요일/시간 설정 확인

### UI가 느릴 때

1. **데이터 정리**: 오래된 매물 삭제
2. **백업 정리**: 불필요한 백업 삭제
3. **재시작**: 프로그램 재시작

---

## 📝 최근 업데이트

### v2.1 (2026-01)

**스크래핑 안정성 대폭 개선:**
- ✅ Selenium 드라이버 세션 자동 복구
- ✅ 연속 빈 결과 감지 및 경고 (3회 연속 시 알림)
- ✅ 중고나라 헤드리스 모드 지원 개선
- ✅ 검색 결과 최신순 정렬 추가
- ✅ 스크래핑 소요 시간 로깅

**알림 시스템 강화:**
- ✅ Discord/Slack 알림 재시도 로직 (3회, 지수 백오프)
- ✅ Telegram 재시도 안정성 개선
- ✅ 상세 오류 메시지 표시

**UI/UX 개선:**
- ✅ 키워드 입력 유효성 검사 (빈값, 플랫폼 미선택 방지)
- ✅ 통계 위젯 메모리 누수 수정 (DB/타이머 정리)
- ✅ 내보내기 오류 메시지 상세화
- ✅ 즐겨찾기 테이블 정렬 기능

**코어 기능:**
- ✅ 자동 태깅 시스템 연동 완료
- ✅ 백업 매니저 GUI 연동
- ✅ 판매 상태 자동 감지
- ✅ 가격 정규화 유틸리티 추가

### v2.0 (2026-01)

- ✅ **자동 태깅 시스템**: 제목 분석 기반 태그 자동 부여
- ✅ **메시지 템플릿**: 판매자 문의 메시지 템플릿
- ✅ **매물 비교**: 여러 매물 나란히 비교
- ✅ **백업/복원**: 자동 백업, 이전 데이터 복원
- ✅ **UI 개선**: 글래스모피즘, 애니메이션
- ✅ **스크래핑 안정화**: Selenium 기반 안정성 개선
- ✅ **가격 추적**: 가격 변동 이력 및 알림

### v1.5 (2025-12)

- ✅ 크롤링 아키텍처 재설계
- ✅ 토스트 알림 추가
- ✅ 테이블 가독성 개선
- ✅ 스레드 안정성 개선

---

## 🛡️ 주의사항

- 이 프로그램은 **개인 사용 목적**으로만 사용하세요.
- 과도한 크롤링은 **IP 차단**을 유발할 수 있습니다.
- 각 플랫폼의 **이용약관**을 준수하세요.
- 상업적 목적의 데이터 수집은 **금지**됩니다.

---

## 📄 라이선스

MIT License

---

## 💡 기여하기

버그 제보, 기능 제안, Pull Request 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
