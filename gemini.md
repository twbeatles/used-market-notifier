# 🤖 Gemini AI 지침서 - 중고거래 알리미 (Used Market Notifier)

> **이 문서는 Gemini AI가 프로젝트를 이해하고 효과적으로 지원하기 위한 포괄적인 가이드입니다.**

---

## 📋 프로젝트 개요

### 목적
당근마켓, 번개장터, 중고나라 등 한국 주요 중고거래 플랫폼을 실시간으로 모니터링하여, 등록된 키워드에 맞는 새 상품이 올라오면 사용자에게 알림을 보내는 데스크톱 애플리케이션입니다.

### 기술 스택
| 카테고리 | 기술 |
|----------|------|
| **언어** | Python 3.10+ |
| **GUI 프레임워크** | PyQt6 |
| **브라우저 자동화** | Playwright (기본), Selenium (레거시) |
| **데이터베이스** | SQLite3 (스레드 안전) |
| **알림** | Telegram Bot API, Discord Webhook, Slack Webhook |
| **빌드** | PyInstaller |

### 지원 플랫폼
| 플랫폼 | 식별자 | 아이콘 | 스크래퍼 |
|--------|--------|--------|----------|
| 당근마켓 | `danggeun` | 🥕 | `scrapers/danggeun.py` |
| 번개장터 | `bunjang` | ⚡ | `scrapers/bunjang.py` |
| 중고나라 | `joonggonara` | 🛒 | `scrapers/joonggonara.py` |

---

## 🏗️ 아키텍처

### 전체 구조

```
used_market_notifier/
├── main.py                 # 애플리케이션 진입점 (GUI/CLI 모드)
├── monitor_engine.py       # 핵심 모니터링 엔진
├── db.py                   # SQLite 데이터베이스 관리자
├── models.py               # 데이터 모델 (dataclass 기반)
├── settings_manager.py     # JSON 기반 설정 관리
├── constants.py            # 전역 상수 정의
├── auto_tagger.py          # 자동 태깅 시스템
├── backup_manager.py       # 백업/복원 관리
├── export_manager.py       # CSV/Excel 내보내기
├── message_templates.py    # 판매자 메시지 템플릿
├── gui/                    # PyQt6 UI 컴포넌트
│   ├── main_window.py      # 메인 윈도우
│   ├── styles.py           # Catppuccin 테마 스타일시트
│   ├── keyword_manager.py  # 키워드 관리 위젯
│   ├── settings_dialog.py  # 설정 다이얼로그
│   ├── listings_widget.py  # 매물 목록 브라우저
│   ├── favorites_widget.py # 즐겨찾기 관리
│   ├── stats_widget.py     # 통계 대시보드
│   ├── components.py       # 재사용 UI 컴포넌트
│   ├── charts.py           # 차트 위젯
│   └── ...
├── scrapers/               # 플랫폼별 스크래퍼
│   ├── base.py             # 추상 베이스 클래스
│   ├── playwright_base.py  # Playwright 기반 베이스
│   ├── stealth.py          # 봇 탐지 우회 (15가지 기법)
│   ├── debug.py            # 스크래핑 디버거
│   ├── danggeun.py         # 당근마켓
│   ├── bunjang.py          # 번개장터
│   └── joonggonara.py      # 중고나라
└── notifiers/              # 알림 모듈
    ├── base.py             # 추상 베이스 클래스
    ├── telegram_notifier.py
    ├── discord_notifier.py
    └── slack_notifier.py
```

### 데이터 흐름

```
[MonitorEngine]
      │
      ├── 1. settings_manager.py → 키워드/설정 로드
      │
      ├── 2. scrapers/*.py → 플랫폼별 검색 실행
      │   └── stealth.py → 봇 탐지 우회
      │
      ├── 3. db.py → 중복 체크, 저장, 가격 변동 추적
      │   └── auto_tagger.py → 자동 태깅
      │
      ├── 4. notifiers/*.py → 알림 전송
      │
      └── 5. PyQt Signal → UI 업데이트
          └── components.py → 카드/뱃지 렌더링
```

---

## 🔑 핵심 데이터 모델

### Item (매물)
```python
@dataclass
class Item:
    platform: str        # 'danggeun', 'bunjang', 'joonggonara'
    article_id: str      # 플랫폼 고유 ID
    title: str           # 상품 제목
    price: str           # 가격 문자열 ("50,000원")
    link: str            # 상세 페이지 URL
    keyword: str         # 검색 키워드
    thumbnail: Optional[str]
    seller: Optional[str]
    location: Optional[str]
    price_numeric: Optional[int]  # 숫자 가격 (필터링용)
```

### SearchKeyword (검색 키워드)
```python
@dataclass
class SearchKeyword:
    keyword: str                    # 검색어
    min_price: Optional[int]        # 최소 가격
    max_price: Optional[int]        # 최대 가격
    location: Optional[str]         # 지역 필터
    exclude_keywords: list[str]     # 제외 키워드
    platforms: list[str]            # 검색 플랫폼
    enabled: bool                   # 활성화 여부
    notify_enabled: bool            # 알림 토글
    custom_interval: Optional[int]  # 개별 검색 주기
    target_price: Optional[int]     # 목표 가격
```

### SaleStatus (판매 상태)
```python
class SaleStatus(Enum):
    FOR_SALE = "for_sale"    # 판매중
    RESERVED = "reserved"    # 예약중
    SOLD = "sold"            # 판매완료
    UNKNOWN = "unknown"      # 상태 미확인
```

### TagRule (자동 태깅 규칙)
```python
@dataclass
class TagRule:
    tag_name: str           # 태그 이름 ("A급", "풀박스" 등)
    keywords: list[str]     # 트리거 키워드
    color: str              # 태그 색상 (#a6e3a1)
    icon: str               # 태그 아이콘 (✨)
    enabled: bool           # 활성화 여부
```

---

## 🎯 주요 기능 모듈

### 1. 자동 태깅 시스템 (`auto_tagger.py`)
상품 제목을 분석하여 자동으로 태그를 부여합니다.

**기본 태그 규칙:**
| 태그 | 트리거 키워드 | 아이콘 |
|------|--------------|--------|
| A급 | A급, 에이급, 상태좋음, 최상, S급 | ✨ |
| 풀박스 | 풀박스, 미개봉, 새제품, 미사용 | 📦 |
| 급처 | 급처, 급매, 빨리, 오늘만 | 🔥 |
| 네고가능 | 네고가능, 네고, 협의가능 | 💬 |
| 택포 | 택포, 택배포함, 무배 | 📮 |
| 직거래 | 직거래, 직거래만 | 🤝 |
| 정품 | 정품, 구매영수증, 보증서 | ✅ |

### 2. 백업 관리자 (`backup_manager.py`)
```python
# 주요 기능
create_backup()           # DB + 설정 ZIP 백업
restore_backup(file)      # 백업 복원
auto_backup_if_needed()   # 자동 주기 백업
cleanup_old_backups(5)    # 오래된 백업 삭제
list_backups()            # 백업 목록 조회
```

### 3. 메시지 템플릿 (`message_templates.py`)
판매자에게 보낼 메시지 템플릿 시스템입니다.

**기본 템플릿:**
- 기본 문의
- 가격 문의  
- 직거래 문의
- 상태 문의
- 구성품 문의
- 당근 안부인사 (당근마켓 전용)
- 번개장터 빠른문의 (번개장터 전용)

**템플릿 변수:**
- `{title}` - 상품 제목
- `{price}` - 판매 가격
- `{seller}` - 판매자 이름
- `{location}` - 지역
- `{target_price}` - 목표 가격
- `{platform}` - 플랫폼 이름

### 4. 내보내기 관리자 (`export_manager.py`)
- CSV 내보내기 (UTF-8 BOM)
- Excel 내보내기 (openpyxl 사용)

---

## 🎨 UI 컴포넌트 가이드

### 재사용 컴포넌트 (`gui/components.py`)

| 컴포넌트 | 용도 |
|----------|------|
| `GlassCard` | 글래스모피즘 카드 (hover 효과) |
| `AnimatedButton` | 프레스 애니메이션 버튼 |
| `PulsingDot` | 상태 표시 점멸 인디케이터 |
| `StatCard` | 통계 표시 카드 (그라디언트) |
| `PlatformBadge` | 플랫폼 아이콘 뱃지 |
| `ToastNotification` | 토스트 알림 |
| `ProgressRing` | 원형 진행률 표시 |

### 스타일 상수 (`gui/styles.py`)

**Catppuccin Mocha 팔레트:**
```python
CATPPUCCIN = {
    'base': '#1e1e2e',      # 메인 배경
    'mantle': '#181825',    # 더 어두운 배경
    'surface0': '#313244',  # 카드 배경
    'surface1': '#45475a',  # 구분선
    'text': '#cdd6f4',      # 기본 텍스트
    'subtext0': '#a6adc8',  # 보조 텍스트
    'blue': '#89b4fa',      # 강조색
    'green': '#a6e3a1',     # 성공/활성
    'red': '#f38ba8',       # 오류/경고
    'yellow': '#f9e2af',    # 주의
    'peach': '#fab387',     # 보조 강조
    'teal': '#94e2d5',      # 정보
    'lavender': '#b4befe',  # 선택됨
}
```

---

## ⚠️ 중요 제약사항

### ❌ 절대 수정 금지 영역

1. **스크래퍼 파싱 로직**
   - `scrapers/danggeun.py`, `bunjang.py`, `joonggonara.py`의 CSS 셀렉터
   - **이유**: 플랫폼 HTML 구조에 민감하게 의존

2. **스텔스 모듈** (`scrapers/stealth.py`)
   - 15가지 봇 탐지 우회 기법:
     - WebDriver 감지 우회
     - Chrome 객체 시뮬레이션
     - 플러그인/언어 위장
     - WebGL 벤더/렌더러 위장
     - Canvas/Audio 핑거프린트 보호
   - **이유**: 수정 시 플랫폼 차단 위험

3. **데이터베이스 스키마**
   - `db.py`의 `create_tables()` 메서드
   - **이유**: 기존 데이터 호환성

### ⚡ 수정 시 주의 영역

| 영역 | 주의사항 |
|------|----------|
| `monitor_engine.py` | 비동기 흐름, QThread 상호작용 |
| GUI 시그널 | 메인 스레드에서만 UI 업데이트 |
| JSON 직렬화 | 기존 설정 파일 호환성 |
| 알림 메시지 | 이모지, 한글 인코딩 |

---

## 🛠️ 개발 가이드라인

### 코드 스타일
```python
# ✅ 타입 힌트 필수
def add_listing(self, item: Item) -> tuple[bool, dict | None, int]:
    """매물 추가 또는 업데이트
    
    Returns:
        (is_new, price_change_info, listing_id)
    """
    pass

# ✅ 로깅 패턴
self.logger.info(f"새 매물 발견: {item.title}")
self.logger.error(f"크롤링 실패: {e}")

# ✅ 한글 주석
# 퍼지 중복 검사: 최근 24시간 내 유사 제목 확인
```

### UI 가이드라인
```python
# ✅ ObjectName 필수 지정 (스타일 적용용)
button.setObjectName("primary")
card.setObjectName("glassCard")

# ✅ 시그널로 UI 업데이트
class MonitorThread(QThread):
    status_update = pyqtSignal(str)
    new_item = pyqtSignal(object)
```

### 비동기 + QThread 패턴
```python
# Windows에서 asyncio 정책 설정
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# QThread 내 asyncio 실행
def run(self):
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)
    try:
        self.loop.run_until_complete(self.engine.start())
    finally:
        self.loop.close()
```

---

## 📦 상수 참조 (`constants.py`)

```python
# 타이밍
SCRAPE_DELAY_SECONDS = 2
DRIVER_WAIT_TIMEOUT = 10
DRIVER_PAGE_LOAD_TIMEOUT = 30
KEYWORD_PAUSE_MS = 2000
AUTO_REFRESH_INTERVAL_MS = 60000

# 재시도
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.0
RETRY_BACKOFF_MULTIPLIER = 2.0

# 페이지네이션/캐시
DEFAULT_PAGE_SIZE = 50
DB_CACHE_TTL_SECONDS = 30

# 백업/정리
DEFAULT_BACKUP_INTERVAL_DAYS = 7
DEFAULT_BACKUP_KEEP_COUNT = 5
DEFAULT_CLEANUP_DAYS = 30

# 플랫폼
PLATFORMS = ['danggeun', 'bunjang', 'joonggonara']
PLATFORM_NAMES = {
    'danggeun': '당근마켓',
    'bunjang': '번개장터',
    'joonggonara': '중고나라',
}
PLATFORM_ICONS = {
    'danggeun': '🥕',
    'bunjang': '⚡',
    'joonggonara': '🛒',
}
```

---

## 🔍 디버깅 가이드

### 로그 확인
- 파일: `notifier.log` (5MB 회전, 3개 백업)
- 레벨: INFO (기본)

### 스크래핑 디버그
```python
# 디버그 모드 활성화
scraper = DanggeunScraper(
    headless=False,       # 브라우저 표시
    debug_mode=True,      # 디버그 모드
    debug_level="verbose" # 상세 로그
)

# 스크린샷 저장
await scraper.take_screenshot("debug_screenshot")
```

### DB 디버그
```sql
-- 최근 매물
SELECT * FROM listings ORDER BY created_at DESC LIMIT 10;

-- 가격 변동
SELECT l.title, ph.old_price, ph.new_price, ph.changed_at
FROM price_history ph JOIN listings l ON ph.listing_id = l.id;

-- 플랫폼별 통계
SELECT platform, COUNT(*) FROM listings GROUP BY platform;
```

---

## 📝 자주 사용하는 패턴

### 새 기능 추가 체크리스트
- [ ] `models.py`에 데이터 클래스 추가
- [ ] `settings_manager.py`에 설정 항목 추가
- [ ] `db.py`에 테이블/쿼리 추가
- [ ] GUI 컴포넌트 구현
- [ ] `gui/styles.py` 스타일 추가
- [ ] 테스트 및 검증

### 새 스크래퍼 추가
```python
from scrapers.playwright_base import PlaywrightScraper
from models import Item

class NewPlatformScraper(PlaywrightScraper):
    PLATFORM = "new_platform"
    BASE_URL = "https://example.com"
    
    async def search(self, keyword: str, location: str = None) -> list[Item]:
        # 1. 검색 페이지 이동
        # 2. 결과 파싱
        # 3. Item 리스트 반환
        pass
```

---

## 📌 요약

| 항목 | 설명 |
|------|------|
| **언어** | Python 3.10+ |
| **GUI** | PyQt6 + Catppuccin Mocha 테마 |
| **DB** | SQLite3 (스레드 세이프) |
| **스크래핑** | Playwright (스텔스 모드) |
| **알림** | Telegram, Discord, Slack |
| **수정 금지** | 스크래퍼 파싱 로직, 스텔스 기법, DB 스키마 |

---

**AI 어시스턴트로서 이 프로젝트를 지원할 때, 위의 제약사항을 준수하고 기존 코드 패턴을 따르세요.**
