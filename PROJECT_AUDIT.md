# Project Audit

## 1. Executive Summary

현재 전체 위험도는 **Low-Medium**입니다. 최초 감사에서 확인한 종료 안정성, 백업 복원 보안, 알림 정책 불일치, 링크 열기 정책, 키워드 가격 검증 문제는 구현 완료되었고 회귀 검증도 통과했습니다.

이번 후속 작업으로 대형 단일 파일도 책임별 패키지로 2차 분할했습니다. 기존 public import 경로는 facade로 유지되어 `from db import DatabaseManager`, `from monitor_engine import MonitorEngine`, `from settings_manager import SettingsManager`, `from scrapers.marketplace_parsers import ...`가 계속 동작합니다.

검증 기준:

- `python -m unittest discover -s tests -q` -> `Ran 91 tests`, `OK`
- `pyright .` -> `0 errors, 0 warnings`
- `git diff --check` -> 통과, CRLF 변환 경고만 출력
- `python scripts/live_smoke.py --keyword 아이폰 --platform all --no-artifacts --summary-file .tmp/live_smoke_summary.json` -> Danggeun/Bunjang/Joonggonara 모두 `ok: true`

## 2. Project Understanding

이 프로젝트는 PyQt6 데스크톱 앱으로, 당근마켓/번개장터/중고나라 매물을 키워드별로 모니터링하고 SQLite에 저장한 뒤 Telegram/Discord/Slack 알림을 보내는 구조입니다.

현재 canonical 구조:

- `main.py`: GUI/CLI 진입점
- `engine/`: `MonitorEngine` 구현
  - `monitor.py`: 엔진 조립 및 상태 보유
  - `scrapers.py`: Playwright/Selenium scraper lifecycle 및 fallback 생성
  - `search_flow.py`: 플랫폼 검색, fallback, quality gate, 필터, DB 저장
  - `metadata.py`: seller/location 보강 및 자동 태깅 보조
  - `notification_runtime.py`: 알림 큐, 재시도, delivery telemetry
  - `runtime.py`: start/stop/close lifecycle
- `storage/`: `DatabaseManager` 구현
  - `schema.py`: schema/migration/integrity
  - `listings.py`: listing write/query, normalized URL, sale status
  - `stats.py`: dashboard/statistics
  - `favorites.py`: favorites/notes
  - `notifications.py`: notification logs
  - `filters.py`: seller filters
  - `maintenance.py`: cleanup/export support
- `app_settings/`: settings serialization, recovery, preset operations
- `scrapers/parsers/`: pure parser helpers for HTML snapshot, normalization, metadata merge, quality gates, URL validation, Bunjang and Joonggonara parsing
- `gui/settings_panels/`, `gui/widgets/*`: SettingsDialog workers/editors and large GUI widget internals

주요 실행 흐름:

1. `main.py`가 GUI/CLI 모드를 선택합니다.
2. GUI에서는 `MainWindow`가 `MonitorThread`와 `MonitorEngine`을 연결합니다.
3. `MonitorEngine.start()`가 scraper/notifier를 초기화하고 반복적으로 `run_cycle()`을 호출합니다.
4. `search_keyword()`가 플랫폼별 검색, fallback, quality gate, metadata enrichment, keyword filter, seller filter, DB persistence, notification queueing을 처리합니다.
5. `DatabaseManager.add_listing()`이 `(platform, article_id)` 우선, `(platform, normalized_url)` 보조 기준으로 중복을 판단하고 가격/판매상태 이력을 기록합니다.

## 3. High-Risk Issues

### 3.1 종료 중 notification worker cancellation

* 위치: `engine/runtime.py`, `engine/notification_runtime.py`
* 문제: 최초 감사 시 `asyncio.CancelledError`가 `Exception`으로 잡히지 않아 shutdown cleanup이 중단될 가능성이 있었습니다.
* 영향: scraper/browser/context close 및 executor shutdown 누락 가능성.
* 근거: notification worker cancel 후 await 경로가 shutdown cleanup 앞에 있었습니다.
* 권장 수정 방향: **구현 완료**. worker cancel 후 `asyncio.CancelledError`를 명시 처리하고 cleanup이 계속 진행되도록 했습니다.
* 우선순위: High -> 완료

### 3.2 백업 ZIP 복원 Zip Slip 방어

* 위치: `backup_manager.py`
* 문제: 최초 감사 시 `extractall()` 기반 복원으로 ZIP entry path traversal 위험이 있었습니다.
* 영향: 악성 백업 ZIP이 restore temp directory 밖에 파일을 쓸 수 있었습니다.
* 근거: backup restore는 사용자 선택 ZIP을 입력으로 받습니다.
* 권장 수정 방향: **구현 완료**. `backup_manifest.json`을 추가하고, `listings.db`, `settings.json`, `backup_info.txt`, `backup_manifest.json` allowlist와 resolved target path 검증을 적용했습니다. manifest 없는 기존 백업도 basename allowlist 기준으로 복원됩니다.
* 우선순위: High -> 완료

### 3.3 알림 정책 불일치

* 위치: `engine/notifications.py`, `engine/notification_runtime.py`, `engine/runtime.py`
* 문제: 최초 감사 시 startup system message가 `notifications_enabled` 및 schedule을 우회할 수 있었습니다.
* 영향: 사용자가 전역 알림을 꺼도 시작 메시지가 외부 채널로 발송될 가능성.
* 근거: 시작 메시지가 일반 item notification 경로와 다른 직접 notifier call을 사용했습니다.
* 권장 수정 방향: **구현 완료**. `NotificationPolicy` helper를 통해 새 매물, 가격 변경, 시스템 시작 메시지가 동일하게 전역 enabled와 schedule 정책을 따릅니다.
* 우선순위: High -> 완료

### 3.4 외부 링크 열기 정책 불일치

* 위치: `gui/link_utils.py`, `gui/listings_widget.py`, `gui/favorites_widget.py`, `gui/stats_widget.py`, `gui/compare_dialog.py`, `gui/message_dialog.py`, `gui/notification_history.py`
* 문제: 최초 감사 시 일부 화면이 `confirm_link_open` 설정을 우회하고 직접 URL을 열었습니다.
* 영향: 사용자가 링크 확인을 켜도 전체 매물/일부 다이얼로그에서는 확인 없이 외부 링크가 열릴 수 있었습니다.
* 근거: `QDesktopServices.openUrl()` 직접 호출 경로가 화면마다 중복되어 있었습니다.
* 권장 수정 방향: **구현 완료**. `open_external_url(parent, engine, url, label=None) -> bool` helper를 추가해 `http`/`https`만 허용하고 설정에 따라 확인 다이얼로그를 거치도록 통합했습니다.
* 우선순위: Medium -> 완료

### 3.5 키워드 가격 범위 검증

* 위치: `gui/widgets/keyword/dialog.py`, `models.py`
* 문제: 최초 감사 시 `min_price > max_price` 입력이 저장될 수 있었습니다.
* 영향: 사용자가 잘못된 가격 범위를 저장하면 가격 있는 매물이 모두 필터링될 수 있었습니다.
* 근거: 기존 dialog validation은 빈 키워드/플랫폼만 검증했습니다.
* 권장 수정 방향: **구현 완료**. 양쪽 가격이 모두 0보다 크고 `min_price > max_price`이면 저장을 막습니다. 가격 미상(`가격문의`, `N/A`, 파싱 실패)은 기존 정책대로 가격 필터를 통과합니다.
* 우선순위: Medium -> 완료

## 4. Potential Functional Gaps

* 추정: 가격 미상 매물을 가격 필터에서 통과시키는 정책은 누락 방지에는 유리하지만, 엄격한 가격 필터를 기대하는 사용자에게는 옵션 분리가 필요할 수 있습니다.
* 추정: `.tmp/live_smoke_summary.json`은 로컬 검증 산출물이므로 Git에 포함하지 않는 현재 `.gitignore` 정책이 맞습니다. 릴리즈 자동화가 생기면 별도 artifacts 저장 정책이 필요합니다.
* 추정: PyInstaller onefile build는 새 local split package를 `used_market_notifier.spec`에서 명시 수집하도록 보강했습니다. 실제 릴리즈 전에는 onefile 빌드와 실행 smoke를 추가로 수행하는 편이 안전합니다.

## 5. Recommended Fix Plan

1단계: 즉시 수정해야 할 문제

- 완료: shutdown cancellation 처리
- 완료: backup restore path traversal 차단
- 완료: notification policy 일관화
- 완료: external link helper 통합
- 완료: keyword price range validation

2단계: 안정성 개선

- 완료: facade import parity test 추가
- 완료: backup manager traversal/manifest compatibility test 추가
- 완료: notification queue/policy test 추가
- 완료: link open policy test 추가
- 완료: keyword validation test 추가
- 완료: live smoke summary-file test 추가

3단계: 구조 개선

- 완료: `storage/`, `engine/`, `app_settings/`, `scrapers/parsers/`, `gui/settings_panels/`, `gui/widgets/*`로 package split
- 완료: 기존 legacy import path는 facade/re-export로 유지
- 완료: `used_market_notifier.spec`, README, Claude/Gemini docs, `.gitignore`를 새 구조에 맞게 갱신

## 6. Test Recommendations

현재 추가된/보강된 테스트:

- `tests/test_notification_queue_flow.py`
- `tests/test_backup_manager.py`
- `tests/test_link_open_policy.py`
- `tests/test_keyword_validation.py`
- `tests/test_live_smoke_summary.py`
- `tests/test_facade_imports.py`

릴리즈 전 권장 검증:

1. `python -m unittest discover -s tests -q`
2. `pyright .`
3. `git diff --check`
4. `python scripts/live_smoke.py --keyword 아이폰 --platform all --no-artifacts --summary-file .tmp/live_smoke_summary.json`
5. `pyinstaller used_market_notifier.spec`
