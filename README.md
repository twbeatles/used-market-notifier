# 🛒 중고거래 알리미 (Used Market Notifier)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.4+-green.svg" alt="PyQt6">
  <img src="https://img.shields.io/badge/Selenium-4.x-orange.svg" alt="Selenium">
  <img src="https://img.shields.io/badge/Playwright-1.50+-blue.svg" alt="Playwright">
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
| **지역 필터** | 당근마켓 best-effort 지역 필터 + 정확도 경고 |
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
| `Ctrl+F` | 제목 검색 (전체 매물) |
| `F` | 즐겨찾기 추가 (전체 매물) |
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

# 브라우저 준비 (Playwright + Selenium)
# - Playwright Chromium 런타임 설치 (권장)
python -m playwright install chromium
# - Chrome(또는 Chromium 기반 브라우저)이 설치되어 있어야 합니다.
# - 드라이버는 webdriver-manager가 자동으로 내려받습니다.

# 실행
python main.py

# regression tests (team standard)
python -m unittest discover -s tests -q
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
   - **지역**: 당근마켓 best-effort 지역 필터
   - **제외 키워드**: "부품", "고장" 등
   - **플랫폼**: 검색할 플랫폼 선택
4. 저장

### 2. 알림 설정

> 참고: Telegram/Discord/Slack 채널을 활성화해도, 전역 설정 `notifications_enabled`가 `true`여야 실제 알림이 전송됩니다.

> 참고: 당근 지역 필터는 현재 세션 지역 기준의 best-effort 검색 후 후처리 필터로 동작합니다. 요청 지역 정확도는 보장되지 않으며, 앱에서 경고를 표시합니다.

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
├── scrapers/            # 플랫폼 스크래퍼 (Playwright 우선 + Selenium 폴백)
│   ├── danggeun.py      # 당근마켓
│   ├── bunjang.py       # 번개장터
│   ├── joonggonara.py   # 중고나라
│   ├── playwright_danggeun.py
│   ├── playwright_bunjang.py
│   ├── playwright_joonggonara.py
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
  "scraper_mode": "playwright_primary",
  "fallback_on_empty_results": true,
  "max_fallback_per_cycle": 3,
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
> - `settings.json`, `listings.db*`, `notifier.log`, `__pycache__/`, `backup/`, `debug_output/`, `.tmp/` 등은 로컬 런타임 데이터로서 Git에 포함되지 않도록 `.gitignore` 처리되어 있습니다.
> - 과거 레거시 설정/알림 샘플 코드는 `legacy/`에 있으며, 현재 메인 앱에서는 사용하지 않습니다.

### 데이터 파일

| 파일 | 설명 |
|------|------|
| `settings.json` | 사용자 설정 |
| `listings.db` | 매물 데이터베이스 |
| `notifier.log` | 로그 파일 |
| `backup/` | 자동 백업 폴더 |
| `debug_output/` | Playwright 디버거 산출물(스크린샷/HTML/네트워크 로그) |

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

### 스크래퍼 모드

| 모드 | 설명 |
|------|------|
| `playwright_primary` | Playwright 우선, 실패/빈결과 시 Selenium 폴백 |
| `selenium_primary` | Selenium 우선, 실패/빈결과 시 Playwright 폴백 |
| `selenium_only` | Selenium만 사용 (폴백 없음) |

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
- 위치/판매자 정보는 플랫폼과 페이지 구조에 따라 제공이 제한될 수 있습니다. 기본 정책은 상세 페이지를 추가로 열지 않는(best-effort) 방식이라 일부 정보가 비어 있을 수 있습니다.

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

## 2026-02 Consistency Update (Dual Engine + Packaging)

This section is the current source of truth and supersedes older statements in this file when conflicts exist.

- Scraper mode supports three values:
  - `playwright_primary` (default)
  - `selenium_primary`
  - `selenium_only`
- Fallback is triggered only when:
  - primary scraper raises an exception, or
  - primary result count is 0 and `fallback_on_empty_results=true`, and
  - per-platform fallback count is below `max_fallback_per_cycle`.
- Result merge dedupe key order:
  - primary key: `(platform, article_id)`
  - secondary key: `url/link`
- Danggeun location policy:
  - if location filter is set, unknown location items are excluded for `danggeun`.
  - app/runtime warns that Danggeun location filtering is best-effort and does not guarantee requested-region accuracy.
- Joonggonara title validity filter:
  - completion keywords are checked by substring match (not exact match).

## 2026-03 Consistency Update (Danggeun/Bunjang Parser)

- Danggeun parser behavior:
  - `article_id` extraction now supports numeric IDs, slug tokens, and deterministic hash fallback.
  - JSON-LD parsing is primary and result intake is capped at top `120` items per search.
  - DOM fallback selector is narrowed to search-result cards only:
    - `a[data-gtm='search_article'][href^='/kr/buy-sell/']`
  - seller enrichment now scans multiple candidate nodes and can recover seller names from profile `aria-label` values when visible text is empty.
- Bunjang parser behavior:
  - Unknown location text (`지역정보 없음` variants) is normalized to `None`.
  - Card text fallback parser removes badge lines (`배송비포함`, `검수가능`) before title/price/location extraction.
  - Detail enrichment is API-first, but still falls back to DOM for missing seller/location fields after partial API responses.
- Location policy impact:
  - Danggeun remains strict when keyword location filter is set.
  - Non-Danggeun platforms keep best-effort behavior with unknown location values.

### Runtime / Build Notes

- Required setup for Playwright path:
  - `python -m playwright install chromium`
- Team-standard regression command:
  - `python -m unittest discover -s tests -q`
- Onefile build command:
  - `pyinstaller used_market_notifier.spec`
- Type-check gate command:
  - `pyright .`
- Type-check baseline is pinned in `pyrightconfig.json`:
  - `pythonVersion=3.10`
  - `typeCheckingMode=standard`
- PyInstaller spec (`used_market_notifier.spec`) includes Playwright Python modules.
- PyInstaller onefile build intentionally excludes `matplotlib`; chart widgets fall back gracefully when unavailable.
- Chromium runtime binaries are not bundled in the EXE.
- If Playwright runtime is unavailable at startup, engine automatically degrades to Selenium mode with warning logs.

## 2026-04 Audit Remediation Update

- Joonggonara parsing / enrichment:
  - Naver search results now accept only Joonggonara article links with numeric `articleid` values.
  - known noise links are rejected before item creation (generic cafe links, URL-only anchors, time/video labels, placeholder text, numeric-only anchor text).
  - detail enrichment now waits for `iframe#cafe_main` and parses seller/location/price/title from the frame body, with outer-page fallback only when the iframe path is unavailable.
  - detail parsing now skips category/UI meta lines, supports `35만원`-style prices, and extracts station/dong-level transaction locations when present.
- Bunjang enrichment / sale status:
  - detail enrichment is API-first and uses the Bunjang product-detail API for seller, location, price, and explicit sale status.
  - seller extraction selectors were updated to the current `/shop/.../products` shape.
  - scraper-provided sale status is normalized to `for_sale`, `reserved`, `sold`, or `unknown`, and DB writes prefer that explicit value over title heuristics.
  - when the detail API omits `seller` or `location`, DOM fallback still tries to fill the missing fields from valid seller candidates and `직거래지역` / `거래지역` labels.
- Observability:
  - Danggeun and Bunjang searches now log per-search candidate counters and drop reasons (`selector_count`, `jsonld_scripts`, `jsonld_items`, `parsed_items`, invalid-title drops, missing-id drops, parse-error drops).
  - when a Playwright search finds candidate DOM/data but still returns `0` parsed items, debug artifacts are dumped under `debug_output/`.
- Metadata enrichment flow:
  - enrichment now uses one shared budget per platform/keyword/cycle.
  - pass 1 enriches only items that need seller/location for location filtering or blocked-seller decisions.
  - pass 2 spends any remaining budget on kept items that still lack seller/location for DB quality and notifications.
- Packaging / tests:
  - `used_market_notifier.spec` now collects Playwright modules plus the `aiohttp` dependency tree used by Bunjang detail enrichment.
  - regression fixtures cover Danggeun, Bunjang, and Joonggonara live markup snapshots plus import safety without `selenium`.

## 2026-04 Stabilization Follow-up

- Playwright lifecycle:
  - Playwright scrapers now use retained async `start/search/enrich/close` resources instead of launching a browser per search/enrichment call.
  - `MonitorEngine` awaits async scrapers directly and keeps Selenium/sync scraper compatibility through the executor path.
  - Playwright health checks now reflect retained browser/context state and recent runtime/parser failures.
- Settings resilience:
  - valid JSON settings are normalized field-by-field instead of quarantining the whole file for a single bad value.
  - `load_recovery_state.normalized_fields` records corrected fields for UI/log diagnostics.
- Data integrity:
  - `listings.normalized_url` is backfilled and indexed.
  - listing writes use `(platform, article_id)` first, then `(platform, normalized_url)` as a secondary duplicate key.
  - schema version is stored in `meta.schema_version` and startup integrity checks verify required columns.
- Notification telemetry:
  - disabled/scheduled-out/no-channel notification decisions are recorded in `notification_delivery_log` with `system` / `skipped_*` statuses.
  - shutdown no longer requeues failed notification retries.
- GUI / packaging / repo hygiene:
  - Settings UI exposes scraper mode, fallback-on-empty, and per-cycle fallback budget.
  - Backup restore stops monitoring first and exits after restore to avoid stale DB connections.
  - `.gitignore` includes `*.pre_restore` restore snapshots.
  - `used_market_notifier.spec` documents the async lifecycle change and standard-library additions.

### Encoding Hygiene Gate

- Track only UTF-8 text files for source/docs.
- Validation target:
  - strict UTF-8 decode failures: `0`
  - `U+FFFD` replacement char occurrences: `0`
  - C1 control chars (`0x80-0x9F`): `0`
- Windows PowerShell에서 한글/이모지가 깨져 보이면 실행 전 `$env:PYTHONIOENCODING='utf-8'` 또는 `chcp 65001`을 적용하세요. 로그 파일은 UTF-8로 기록됩니다.

### Quick Smoke Checklist

1. Configure one keyword per platform.
2. Run one monitoring cycle.
3. Verify per-platform scrape log line includes:
   - `primary_engine`, `primary_count`, `fallback_used`, `fallback_count`, `fallback_reason`, `elapsed_ms`
4. Confirm new listings are persisted in DB.

## 2026-03 Consistency Update (Data Integrity + Notification Reliability)

This section is the current source of truth for the March 25, 2026 stabilization work.

- Listing persistence:
  - auto tags are stored in `listing_auto_tags`, not in `listing_notes.auto_tags`
  - existing listings refresh non-empty `title`, `url`, `thumbnail`, `seller`, and `location`
  - `keyword` remains the original representative keyword for the listing row
  - `sale_status` is re-detected every cycle and state transitions are recorded in `sale_status_history`
- Notification delivery:
  - the first monitoring cycle skips both new-item notifications and price-change notifications
  - retries happen per channel, not per whole notification job
  - successful sends are recorded in `notification_log`
  - channel success/failure/retry telemetry is recorded in `notification_delivery_log`
  - the notification history UI now shows a 7-day channel health summary
- Metadata enrichment:
  - `metadata_enrichment_enabled` defaults to `false`
  - when enabled, seller/location enrichment uses a two-phase budget: targeted prefilter enrichment for location/seller-block decisions, then postfilter enrichment for kept items still missing metadata
  - enrichment is capped at `10` items per platform per keyword per cycle
  - failures are warning-only and do not discard the base search result
  - explicit scraper-provided `sale_status` values are persisted when available
- Import/runtime safety:
  - the package can be imported in Playwright-only environments even when `selenium` is not installed
  - Selenium scraper classes are treated as optional runtime dependencies and are skipped with informative logs when unavailable
- Cleanup / recovery semantics:
  - `cleanup_exclude_noted` protects only rows that have real `listing_notes`
  - auto tags alone do not protect a listing from cleanup
  - cleanup explicitly removes linked rows from favorites, notes, auto tags, notification logs, delivery logs, price history, and sale-status history
  - broken settings files are renamed to `settings.broken-YYYYMMDD_HHMMSS.json`
  - startup recovery restores the newest valid `backup_*.zip` settings payload when available, otherwise defaults are used
  - GUI startup shows a recovery notice when this path is taken
- CLI / packaging:
  - `python main.py --headless` is a session-only override and does not rewrite `settings.json`
  - `used_market_notifier.spec` excludes `tests` and `legacy` from onefile builds
  - `.gitignore` must ignore `settings.broken-*.json`, `*.pre_restore`, rotated logs like `notifier.log.1`, and workspace-local temp directories such as `.tmp/`

### Verification Baseline

- Regression tests:
  - `python -m unittest discover -s tests -q`
- Restricted/sandboxed shells:
  - point `TEMP/TMP` to workspace-local `.tmp/` before running regression tests
- Type checks:
  - `pyright .`
- Current expected baseline after this update:
  - `Ran 70 tests`
  - `OK`
