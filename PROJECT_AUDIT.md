# Project Audit

> 감사일: 2026-09-28 · 대상 커밋: `3f4857a` (main, v1.1.1) · 범위: 기능 구현·런타임 안정성
> 코드는 수정하지 않았습니다. 재현은 모두 임시 디렉터리(스크래치 패드)의 격리된 DB/설정 파일로 수행했고, 저장소의 `listings.db`·`settings.json`·`backup/`은 건드리지 않았습니다.
> 이전 감사(2026-06, `d7afc5d`)의 조치 완료 항목(Zip Slip 방어, CancelledError 종료 처리, 시스템 알림 정책 통일 등)은 이번 감사에서 회귀 여부만 확인했으며 재지적하지 않습니다.

---

## 0. 조치 상태 (2026-09-28 remediation)

아래 본문(1~9장)은 감사 시점 기록이며, 모든 항목은 `specs/001-audit-remediation/`(spec → plan → tasks)에 따라 수정되었습니다. 각 결함의 재현 시나리오는 네트워크 없는 회귀 테스트로 추가했습니다.

| 이슈 | 상태 | 조치 요약 | 회귀 테스트 |
|------|------|-----------|-------------|
| ISSUE-001 복원 WAL 손상 | 수정 | SQLite online backup API로 복원, 백업 DB 무결성 사전 검사, pre_restore도 backup API 스냅샷 | `tests/test_restore_live_db.py` |
| ISSUE-002 알림 기준선 | 수정 | `search_baselines` 테이블로 (검색 조건 서명, 플랫폼) 기준선, 프로세스 첫 엔진만 첫 사이클 억제, 사이클 알림 상한 15 + 요약 | `tests/test_notification_baseline.py` |
| ISSUE-003 SettingsPage host | 수정 | `gui/settings_panels/host.py`로 host 해석, 복원/정리 전 대기형 중지(실패 시 거부), 차단 판매자 조회/해제 복구 | `tests/test_settings_host.py` |
| ISSUE-004 가격 왕복 | 수정 | 미상 가격은 기존 가격 유지·변동 미기록, 보강 시 stale `price_numeric` 재계산 | `tests/test_listing_price_status_rules.py` |
| ISSUE-005 보강 중 primary 재기동 | 수정 | 폴백 없으면 보강 폴백 단계 생략, 폴백 지연 생성·600초 쿨다운·폴백 단독 교체 | `tests/test_fallback_lifecycle.py` |
| ISSUE-006 중지 블로킹 | 수정 | `request_stop()` 비블로킹, 키워드/플랫폼 경계 중지 확인, 스레드 참조 유지, 재시작 직렬화 | `tests/test_monitor_stop.py` |
| ISSUE-007 마이그레이션 500행 | 수정 | 읽기 커서 분리, `PRICE_PARSE_VERSION=3`으로 부분 처리 DB 재계산 | `tests/test_price_migration_batches.py` |
| ISSUE-008 수식 인젝션 | 수정 | `sanitize_cell()` 접두 처리, xlsx 문자열 셀 강제 | `tests/test_export_sanitize.py` |
| ISSUE-009 Windows CLI 루프 | 수정 | 이벤트 루프 정책 API 제거, GUI 스레드는 Proactor 루프 직접 생성 | `tests/test_event_loop_policy.py` |
| ISSUE-010 CWD 의존 경로 | 수정 | `app_paths.ensure_app_root_cwd()`, 로그 파일 실패 시 콘솔 전용으로 기동 | `tests/test_app_paths.py` |
| ISSUE-011 판매 상태 역전 | 수정 | 증거 없으면 기존 상태 유지 | `tests/test_listing_price_status_rules.py` |
| 갭: 정리 기준 | 수정 | `listing_last_seen` 테이블, `COALESCE(last_seen, created_at)` 기준 | `tests/test_cleanup_last_seen.py` |
| 갭: 단일 인스턴스 | 수정 | `QLockFile` 가드(stale lock 자동 처리) | `tests/test_single_instance.py` |
| 갭: 설정 비원자 저장 | 수정 | 임시 파일 + `os.replace` | `tests/test_settings_secrets.py` |
| 갭: 자격 증명 평문 | 수정 | Windows DPAPI(`dpapi:v1:`), 평문 호환, 복호화 실패 안내 | `tests/test_settings_secrets.py` |
| 갭: 폴백 즉시 생성 | 수정 | 지연 생성 | `tests/test_fallback_lifecycle.py` |
| 갭: 간격 식별자 (+추가 발견: UTC 비교 오류) | 수정 | 서명+플랫폼 키, `checked_at`을 UTC로 비교(기존에는 KST에서 540분 미만 간격이 항상 경과 처리) | `tests/test_keyword_interval.py` |
| 문서 불일치 | 수정 | README/CLAUDE.md 정정, `claude.md` → `CLAUDE.md`, `AGENTS.md` 추가 | — |

검증: `python -m unittest discover -s tests -q` → `Ran 218 tests` / `OK`, `pyright .` → 0 errors, GUI 스모크(`USED_NOTIFIER_GUI_SMOKE=1`)와 `main.py --smoke` 통과. 실제 사이트 스모크와 메신저 실발송, onefile 빌드는 이번에도 실행하지 않았습니다.

---

## 1. Executive Summary

**전체 상태:** 엔진/스토리지 계층은 책임 분리가 잘 되어 있고 162개 단위 테스트가 모두 통과합니다. 업데이트 경로(Ed25519 서명, HTTPS, SHA-256, 스모크 후 롤백)와 백업 ZIP 검증은 견고합니다. 그러나 **2026-09 Fluent 셸 전환 이후 GUI↔엔진 연결부**와 **"알림 기준선(첫 사이클 억제)" 설계**에서 실제로 재현되는 결함이 있습니다.

**전체 위험도: High** — 데이터 손상이 실제로 재현되는 경로가 1개 있습니다.

**가장 중요한 문제**

| # | 문제 | 심각도 | 신뢰도 |
|---|------|--------|--------|
| ISSUE-001 | 백업 복원이 열려 있는 WAL DB 위에 파일을 덮어써 **DB 손상(`database disk image is malformed`) 또는 복원이 조용히 무효화** | Critical | Confirmed (재현) |
| ISSUE-002 | 알림 기준선이 엔진 인스턴스 단위 → **모니터링 중 키워드 추가 시 기존 매물 전체 알림 폭주**, 설정 저장 시에는 반대로 **신규 매물 알림 누락** | High | Confirmed (재현) |
| ISSUE-003 | Fluent `SettingsPage.parent()`가 MainWindow가 아님 → **복원/정리 전에 모니터링이 중지되지 않고**, 차단 판매자 목록/해제 기능이 **항상 동작하지 않음** | High | Confirmed (런타임 확인) |
| ISSUE-004 | 중고나라 가격이 `가격문의 ↔ 실제가`로 왕복하며 **가짜 가격 변동 알림과 `price_history` 오염** | Medium | Confirmed (DB 레벨 재현) |
| ISSUE-005 | 폴백이 없는 플랫폼에서 메타데이터 보강 1건마다 **primary 브라우저 전체 재기동** | Medium | Confirmed (재현) |

**데이터 손상/유실 가능성:** **있음.** ISSUE-001은 GUI에서 복원 기능을 쓰면 거의 항상 발생 조건이 성립합니다(MainWindow가 DB 연결을 앱 수명 동안 열어 둠). `.pre_restore` 스냅샷도 `-wal` 파일 없이 메인 파일만 복사하므로 최근 변경분이 빠진 불완전 사본입니다. ISSUE-007(가격 마이그레이션 조기 종료)은 레거시 DB에서 `price_numeric` 값이 영구적으로 틀린 채 남게 합니다.

**가장 먼저 수정할 영역:** ① 백업 복원 경로(ISSUE-001 + ISSUE-003), ② 알림 기준선 설계(ISSUE-002), ③ `listings` 갱신 정책의 "알 수 없는 가격" 처리(ISSUE-004).

---

## 2. Project Understanding

**목적:** 당근마켓/번개장터/중고나라를 키워드별로 주기적으로 스크래핑하고, 새 매물·가격 변동을 SQLite에 기록한 뒤 Telegram/Discord/Slack과 트레이로 알리는 Windows 중심 PySide6(Fluent) 데스크톱 앱입니다. CLI 모드도 지원합니다.

**주요 entrypoint**

| Entry | 경로 |
|-------|------|
| GUI | `main.py:main` → `run_gui` → `gui/app.py:main` → `gui/main/window.py:MainWindow` |
| CLI | `main.py --cli` → `run_cli` → `asyncio.run(MonitorEngine.start())` |
| 업데이트 확인 / 적용 헬퍼 | `main.py --check-update` / `--apply-update` → `updater/apply.py:handle_apply_update` |
| 스모크 | `main.py --smoke` → `updater/smoke.py` |

**핵심 모듈**

- `engine/` — `MonitorEngine` (mixin 조립: `runtime`, `search_flow`, `scrapers`, `metadata`, `notification_sections/*`)
- `storage/` — `DatabaseManager` (단일 `sqlite3` 연결 + `threading.Lock`, WAL 모드)
- `app_settings/` — `SettingsManager` (JSON, 필드 단위 정규화 + 손상 파일 격리/백업 복구)
- `scrapers/` — Playwright/Selenium 이중 엔진, `scrapers/parsers/*` 순수 파서
- `notifiers/` — aiohttp 기반 Telegram/Discord/Slack (채널별 재시도, 429 처리)
- `backup/` — ZIP 백업(생성은 SQLite backup API), 매니페스트/basename allowlist 복원
- `updater/` — 서명 매니페스트 검증, exe 교체 + `--smoke` 실패 시 롤백
- `gui/` — `MSFluentWindow` 셸, `gui/pages/*`, `gui/widgets/*`, `gui/settings_panels/mixins/*`(SettingsPage가 재사용)

**데이터 저장**

- `listings.db` (SQLite, WAL, `synchronous=NORMAL`): `listings`, `price_history`, `favorites`, `listing_notes`, `listing_auto_tags`, `sale_status_history`, `notification_log`, `notification_delivery_log`, `search_stats`, `seller_filters`, `meta`
- `settings.json` (평문, 알림 토큰/웹훅 포함), `notifier.log` (5MB×3 회전), `backup/backup_*.zip`
- 위 경로는 모두 **현재 작업 디렉터리(CWD) 기준 상대 경로**입니다. 업데이터만 `app_storage_root()`(exe 폴더)를 씁니다.

**외부 의존성:** Naver 검색(중고나라), 당근/번개장터 웹·API, Telegram Bot API, Discord/Slack 웹훅, GitHub Releases(업데이트), Playwright Chromium / Chrome+Selenium.

**핵심 실행 흐름**

```
[GUI] 모니터링 시작 버튼
  → MonitoringMixin.start_monitoring()           (새 MonitorEngine + MonitorThread 생성, DB는 MainWindow.db 공유)
  → MonitorThread.run()  (Proactor 루프)
  → MonitorEngine.start()  → initialize_scrapers() / initialize_notifiers() / 알림 워커 시작
  → loop: run_cycle()
        → for keyword: search_keyword()
             → scrape_platform() ×N (Semaphore 2, primary → [예외/0건/malformed] → fallback, 백오프)
             → _enrich_items_with_budget(prefilter) → SearchKeyword.matches() → 차단 판매자 제외
             → _enrich_items_with_budget(postfilter)
             → DatabaseManager.is_fuzzy_duplicate() / add_listing()     ← DB 쓰기
             → is_new → on_new_item(Qt Signal) + send_notifications() → asyncio.Queue
             → price_change → on_price_change + send_notifications(is_price_change=True)
             → record_search_stats()
  → notification worker → Notifier.send_*() → notification_log / notification_delivery_log
```

```
[GUI] 설정 > 유지보수 > 선택 백업 복원
  → MaintenanceSettingsMixin.restore_selected_backup()
  → (parent().monitor_thread 확인 → 모니터링 중지)   ← Fluent 셸에서는 실행되지 않음 (ISSUE-003)
  → BackupManager.restore_backup() → shutil.copy2(temp_db, listings.db)   ← 열린 WAL 연결 위에 덮어씀 (ISSUE-001)
  → QApplication.quit()
```

---

## 3. Audit Coverage & Limitations

**직접 확인한 모듈 (전체 소스 열람)**

- `main.py`, `engine/runtime.py`, `engine/search_flow.py`, `engine/metadata.py`, `engine/scrapers.py`, `engine/notifications.py`, `engine/notification_sections/*`, `engine/monitor.py`
- `storage/database.py`, `storage/listings.py`, `storage/schema.py`, `storage/maintenance.py`
- `app_settings/manager.py`, `models/search_keyword.py`, `price_utils.py`
- `backup/mixins/restorer.py`, `updater/apply.py`, `updater/installer.py`(적용/헬퍼 부분), `updater/manifest.py`(검증 부분)
- `gui/main/threads.py`, `gui/main/window.py`(초기화), `gui/main/window_mixins/monitoring.py`, `lifecycle.py`, `gui/pages/settings_page.py`, `gui/pages/update_page.py`(host 해석), `gui/settings_panels/mixins/maintenance.py`, `seller.py`, `gui/widgets/keyword/widget.py`
- `notifiers/base.py`, `notifiers/telegram_notifier.py`(Discord/Slack은 timeout/429 처리만 확인), `export_manager.py`
- `scrapers/parsers/joonggonara.py`, `scrapers/playwright_joonggonara.py`(enrich), `scrapers/selenium_base.py`(드라이버 생성 시점)

**CodeGraph 사용 범위 (정직한 기록)**

- `codegraph_explore`로 `MonitorEngine.start/stop/close/run_cycle` 호출 흐름과 blast radius를 확인했습니다: `MonitorThread.stop → engine.close → engine.stop`, `run_cycle`의 caller(`engine/runtime.py`), `close`의 caller 6곳(`gui/main/threads.py`, listings/stats 위젯 `closeEvent`, `gui/main/window_mixins/updater.py` 등).
- 이후의 caller/callee 확인(`keywords_changed` 수신자, `remove_seller_filter`/`get_blocked_sellers` 호출부, `self.parent()` 사용처, 상대 경로 사용처)은 **grep과 파일 직접 열람**으로 수행했습니다. CodeGraph 결과가 파일 일부만 발췌해 주는 경우가 많아, 핵심 파일은 전체를 직접 읽었습니다.

**실행한 검증**

| 검증 | 결과 |
|------|------|
| `python -m unittest discover -s tests -q` (`.venv`, `QT_QPA_PLATFORM=offscreen`) | `Ran 162 tests` / `OK` |
| MainWindow 오프스크린 생성 후 `settings_page.parent()` / `_get_parent_db()` / `keywords_changed` 수신자 확인 | `PopUpAniStackedWidget`, `None`, `0` |
| 열린 WAL 연결 상태에서 `BackupManager.restore_backup()` 후 재오픈 | `database disk image is malformed` (300행 WAL) / 복원 무효화(1행 WAL) |
| 가짜 스크래퍼로 `run_cycle` 3회, 3회차 전에 키워드 추가 | 새 키워드의 기존 매물 40건 전부 알림 큐 투입 |
| `add_listing` 가격 왕복 / 상태 역전 / stale `price_numeric` | 각각 재현 (ISSUE-004, 010) |
| 가격 마이그레이션(`price_parse_version=1`, 1200행) | 500행만 재계산, 버전은 2로 기록 |
| 폴백 없는 플랫폼에서 보강 10회 | primary 스크래퍼 10회 close+재생성 |
| 실제 `MonitorThread` + 느린 cleanup 가짜 엔진으로 `stop_monitoring` 절차 재현 | UI 스레드 10.0초 블로킹, `wait(5000)` 후에도 스레드 실행 중 |
| 이벤트 루프 정책별 Playwright 런타임 probe | Selector: `NotImplementedError`(subprocess 미지원) |
| `ExportManager.export_to_excel` / `export_to_csv`에 `=`로 시작하는 제목 | xlsx 셀 `data_type='f'`(수식), CSV 원문 그대로 |

**확인하지 못한 것 / 한계**

- **실제 사이트 스크래핑**(`scripts/live_smoke.py`)은 실행하지 않았습니다(네트워크·봇 탐지·이용 약관 영향). 이 환경에는 Playwright Chromium 런타임이 설치되어 있지 않습니다.
- Telegram/Discord/Slack 실제 전송, GitHub Release 업데이트 적용, PyInstaller onefile 빌드는 실행하지 않았습니다.
- `pyright`는 실행하지 않았습니다.
- 스크래퍼 파싱 로직과 `stealth.py`는 CLAUDE.md의 "수정 금지" 영역이고 사이트 의존성이 커서 정적 검토에서 제외했습니다.
- GUI 위젯 중 compare/favorites/stats/listings 내부 로직과 메시지 템플릿·자동 태깅 UI는 표본만 확인했습니다.
- macOS/Linux에서는 실행하지 않았습니다. 크로스플랫폼 항목은 코드 근거입니다.
- 요청된 `AGENTS.md`는 저장소에 존재하지 않습니다.

---

## 4. High-Risk Issues

### [ISSUE-001] 백업 복원이 열린 WAL DB 위에 파일을 덮어써 DB 손상 또는 복원 무효화

* **위치:** `backup/mixins/restorer.py` / `RestorerMixin.restore_backup` (L64-71); 호출부 `gui/settings_panels/mixins/maintenance.py` / `restore_selected_backup` (L202-251); 연결 보유 `gui/main/window.py` L70 (`self.db = DatabaseManager(...)`); WAL 설정 `storage/database.py` L43
* **우선순위:** Critical
* **신뢰도:** Confirmed (격리 환경 재현)
* **문제:** 복원은 `shutil.copy2(temp_db, db_path)`로 메인 DB 파일만 교체합니다. 이때 MainWindow의 공유 연결(WAL 모드)은 열려 있고, `listings.db-wal`/`-shm`은 그대로 남습니다. 연결이 닫히거나(체크포인트) 다음 실행에서 WAL이 재생되면, **이전 DB의 WAL 프레임이 복원된 파일 위에 덮어써집니다.**
* **발생 조건:** GUI에서 "선택 백업 복원"을 실행하는 모든 경우. `MainWindow.db`는 앱 수명 내내 열려 있고, 복원 코드에는 "Do not forcibly close parent.engine.db" 주석과 함께 연결을 닫지 않는다는 의도가 명시되어 있습니다. 모니터링 중이면(ISSUE-003으로 실제로 중지되지 않음) 엔진이 계속 쓰므로 위험이 더 커집니다.
* **영향:**
  - WAL에 체크포인트되지 않은 페이지가 많을 때: 재오픈 시 `sqlite3.DatabaseError: database disk image is malformed`. 앱이 DB를 열지 못함.
  - WAL이 작을 때: `integrity_check=ok`이지만 행 수가 복원 전 상태로 돌아가, 사용자는 복원이 성공했다고 믿지만 실제로는 무효입니다.
  - `.pre_restore`는 메인 파일만 복사하므로(L69) WAL에만 있던 최근 변경은 스냅샷에서도 빠집니다.
* **근거 (재현):** 임시 폴더에서 `DatabaseManager`로 50행 기록 → 체크포인트 → `create_backup()` → 300행 추가(WAL 4.1MB) → `restore_backup()` → 연결 close → 재오픈 시 `database disk image is malformed`. 두 번째 시나리오(200행 → 백업 → 1행 추가 → 복원)에서는 기대 200행에 대해 201행이 남아 복원이 무효화되었습니다. 기존 테스트 `tests/test_backup_manager.py`(L87)는 **열린 연결이 없는 상태**에서만 복원을 검증합니다.
* **반증 확인:**
  - "복원 후 앱 종료"(`QApplication.quit()`)는 손상을 막지 못합니다. 종료 시 연결 해제가 오히려 WAL을 체크포인트해 손상을 확정합니다. 재현의 `close` 모드와 같습니다.
  - Windows에서 열린 SQLite 파일은 `FILE_SHARE_WRITE`로 열려 있어 `copy2`가 차단되지 않습니다(재현에서 `restore ok: True`).
  - 백업 **생성** 쪽은 SQLite backup API를 사용하므로 안전합니다. 문제는 복원 쪽에만 있습니다.
* **호출/영향 범위:** `SettingsPage`(유지보수 탭) → `restore_selected_backup` → `BackupManager.restore_backup`. 영향: `listings.db` 전체(매물·즐겨찾기·메모·가격 이력·알림 로그), 다음 실행 시 `MainWindow.__init__`의 `DatabaseManager` 생성 실패 → 앱 시작 불가.
* **권장 수정 방향:**
  1. 파일 복사 대신 SQLite backup API로 **열린 연결에 직접 복원**합니다: `sqlite3.connect(temp_db).backup(live_db.conn)`. 락은 `DatabaseManager.lock` 안에서 잡습니다.
  2. 또는 "보류 중 복원" 마커를 남기고, 다음 시작 시 **어떤 연결도 열기 전에** 교체하면서 `-wal`/`-shm`을 정리합니다.
  3. `.pre_restore`도 backup API로 만들어 WAL 내용을 포함시킵니다.
  4. 복원 전에 모니터링 중지를 **동기적으로 보장**합니다(ISSUE-003).
* **필요한 회귀 테스트:** 열린 `DatabaseManager`에 WAL 미체크포인트 행을 남긴 상태로 복원 → 연결 close → 재오픈 → `PRAGMA integrity_check == ok` 이고 행 수 == 백업 시점 행 수. `.pre_restore`를 열었을 때 복원 직전 행 수와 같아야 합니다.

---

### [ISSUE-002] 알림 기준선이 엔진 인스턴스 단위 — 키워드 추가 시 알림 폭주, 설정 저장 시 알림 누락

* **위치:** `engine/monitor.py` L46 (`is_first_run = True`); `engine/search_flow.py` L313, L331(알림 조건), L416-417(첫 사이클 종료 시 False); `gui/widgets/keyword/widget.py` `keywords_changed`(L11, 수신자 없음); `gui/main/window_mixins/monitoring.py` `_apply_settings_after_save` (L123-133)
* **우선순위:** High
* **신뢰도:** Confirmed (가짜 스크래퍼로 엔진 레벨 재현)
* **문제:** "첫 사이클 알림 억제"가 **엔진 인스턴스당 1회**입니다. 키워드별·플랫폼별 기준선이 없습니다.
  - (a) 모니터링 중 키워드를 추가·수정(텍스트 변경)·재활성화하면, 설정 객체가 엔진과 공유되어 다음 사이클에 곧바로 검색됩니다. `is_first_run`은 이미 False이므로 **검색 결과 전체(플랫폼당 최대 약 120건)가 "새 매물"로 외부 채널에 발송**됩니다. `keywords_changed` 시그널에는 연결된 슬롯이 없어 엔진 재시작도 일어나지 않습니다(런타임 수신자 0 확인).
  - (b) 첫 사이클에 특정 플랫폼이 실패하거나 백오프된 뒤 이후 사이클에서 처음 성공해도, DB에 없던 그 플랫폼의 기존 매물이 모두 알림으로 나갑니다.
  - (c) 반대로, 설정 페이지에서 "저장"하면 모니터링 중일 때 `stop_monitoring()` → `start_monitoring()`으로 **새 엔진**이 만들어져 `is_first_run=True`가 됩니다. 직전 사이클 이후 실제로 올라온 신규 매물이 **외부 알림·트레이 알림 없이 DB에만 저장**됩니다.
* **발생 조건:** (a) 모니터링 중 키워드 페이지에서 추가/편집/토글. README의 기본 사용 흐름입니다. (c) 모니터링 중 설정 저장.
* **영향:** Telegram/Discord/Slack 스팸과 레이트리밋(429). 알림 큐 적체로 실제 신규 매물 알림이 지연되고, `notification_log`가 오염됩니다. (c)에서는 핵심 기능(새 매물 알림)이 조용히 누락됩니다.
* **근거 (재현):** `FakeScraper`(키워드당 40건) + `selenium_only` 모드 엔진에서 `run_cycle` 1회차 0건, 2회차 0건을 확인했습니다. 3회차 전 `settings.keywords.append(SearchKeyword("맥북"))` 후 `send_notifications`가 **40회** 호출되었습니다(전부 기존 매물).
* **반증 확인:**
  - 퍼지 중복 검사(`is_fuzzy_duplicate`)는 같은 플랫폼·같은 가격 문자열·유사 제목만 거르므로, 서로 다른 매물을 막지 못합니다.
  - `notify_enabled`는 키워드별 수동 스위치일 뿐 기준선 역할을 하지 않습니다.
  - 알림 큐에 사이클당 발송 상한이나 다이제스트가 없습니다(`queue.py`는 20건 이상일 때 경고 로그만 남김).
  - `custom_interval`은 첫 사이클에서 새 키워드를 건너뛰지 않으므로(최근 검색 시각이 없음) 폭주를 막지 못합니다.
* **호출/영향 범위:** `KeywordManagerWidget.add_keyword/edit_keyword/toggle_keyword` → `SettingsManager`(엔진과 공유 객체) → `run_cycle` → `search_keyword` → `send_notifications` → 알림 워커 → 모든 notifier. `SettingsPage._on_save_clicked` → `_apply_settings_after_save` → `stop_monitoring/start_monitoring`.
* **권장 수정 방향:**
  1. 기준선을 `(keyword, platform)` 단위로 관리합니다. 예: `search_stats`에 해당 쌍의 성공 기록이 없으면 그 검색 결과는 알림 없이 저장만 합니다(첫 성공 검색 = 기준선). 이렇게 하면 엔진 재시작에도 기준선이 유지되므로 (c)가 해결됩니다.
  2. 엔진 재시작 시에는 DB 기준 기준선만 쓰고 `is_first_run` 전역 억제는 제거(또는 기준선 부재 시에만 적용)합니다.
  3. 안전장치로 사이클당·키워드당 알림 상한과 초과분 요약 메시지를 둡니다.
* **필요한 회귀 테스트:** (a) 사이클 2회 후 키워드 추가 → 3회차 알림 0건, 4회차에 새로 등장한 매물만 알림. (b) 1회차에 플랫폼 A 예외 → 2회차 성공 → 알림 0건. (c) 엔진 A에서 사이클 1회 → 엔진 B(같은 DB)로 교체 → B의 첫 사이클에서 새로 등장한 매물 1건은 알림 1건.

---

### [ISSUE-003] Fluent SettingsPage에서 `self.parent()`가 MainWindow가 아님 — 복원/정리 전 모니터링 미중지, 차단 판매자 관리 불능

* **위치:** `gui/settings_panels/mixins/maintenance.py` L223-230(복원), L277-289(지금 정리), L323(정리 후 새로고침); `gui/settings_panels/mixins/seller.py` L62-66, L96-99; `gui/pages/settings_page.py` `_get_parent_db` (L120-125)
* **우선순위:** High
* **신뢰도:** Confirmed (오프스크린 MainWindow 런타임 확인)
* **문제:** `SettingsPage`는 `addSubInterface`로 Fluent 스택 위젯에 재부모화됩니다. 그래서 `self.parent()`는 `PopUpAniStackedWidget`이 되고, `monitor_thread`·`stop_monitoring`·`engine` 속성이 없습니다. 레거시 `SettingsDialog`용으로 작성된 mixin 코드가 그대로 재사용되면서 모든 `getattr(parent, ...)`가 조용히 `None`을 돌려줍니다(예외가 `except Exception: pass`로 삼켜짐).
* **발생 조건 / 영향:**
  1. **복원:** 모니터링 중이어도 중지하지 않고 복원을 진행합니다. 엔진이 복원 도중과 직후에도 DB에 쓰고, 이어 `QApplication.quit()`가 실행 중인 스레드를 남긴 채 종료합니다. ISSUE-001의 손상 가능성이 커집니다.
  2. **지금 정리 실행:** "모니터링을 중지할까요?" 확인창이 뜨지 않고, 모니터링과 동시에 별도 연결로 삭제를 실행합니다. 정리는 `created_at` 기준이라, 아직 검색 결과에 남아 있는 오래된 매물이 삭제된 뒤 다음 사이클에서 `add_listing`이 **새 매물로 판정해 다시 알림**을 보냅니다(`is_first_run=False`이므로).
  3. **차단 판매자 탭:** `load_blocked_sellers()`가 즉시 return하므로 목록이 항상 비어 있습니다. `unblock_seller()`는 항상 "데이터베이스 연결을 찾을 수 없습니다"로 실패합니다. 차단 해제 UI는 이 탭뿐이므로(`remove_seller_filter` 호출부 1곳), **한 번 차단한 판매자는 GUI로 해제할 수 없습니다.**
  4. 정리 완료 후 통계/목록 자동 새로고침도 동작하지 않습니다(L323).
* **근거:** 격리된 설정/DB로 `MainWindow`를 오프스크린 생성한 결과: `settings_page.parent()` → `PopUpAniStackedWidget`, `is MainWindow: False`, `hasattr(parent, "monitor_thread") == False`, `_get_parent_db() → None`. `settings_page.window() is MainWindow → True`입니다(올바른 해석 경로가 존재함). 같은 문제를 이미 알고 있던 `gui/pages/update_page.py`는 `self.window()`를 먼저 사용합니다.
* **반증 확인:** 복원/정리/차단 관리 UI는 `SettingsPage`에만 존재합니다(`SettingsDialog`는 셸에서 열리지 않음). `FluentChromeContractTest` 등 기존 테스트는 페이지 구성만 검증하고 host 해석은 검증하지 않습니다.
* **호출/영향 범위:** `MaintenanceSettingsMixin.restore_selected_backup`, `run_cleanup_now`, `_on_cleanup_done`, `SellerSettingsMixin.load_blocked_sellers`, `unblock_seller`, `SettingsPersistenceMixin`(L68에서 `load_blocked_sellers` 호출). 영향: DB 무결성(ISSUE-001 가중), 중복 알림, 판매자 필터 관리.
* **권장 수정 방향:** mixin에서 `self.parent()` 대신 `self.window()`를 쓰거나, 더 명확하게는 `SettingsPage` 생성 시 `host`(stop/start 콜백, DB, monitor 상태 조회)를 **명시적으로 주입**합니다. host를 찾지 못하면 조용히 넘어가지 말고 복원/정리를 **거부**해야 합니다.
* **필요한 회귀 테스트:** 오프스크린 `MainWindow`에서 (1) `settings_page`의 host 해석 결과가 MainWindow, (2) 모니터링 실행 상태(가짜 thread)에서 `restore_selected_backup`가 `stop_monitoring`을 호출, (3) `add_seller_filter` 후 차단 탭 행 수 1 → 해제 후 0.

---

### [ISSUE-004] 중고나라 가격 `가격문의 ↔ 실제가` 왕복으로 가짜 가격 변동 알림 및 가격 이력 오염

* **위치:** `storage/listings.py` / `add_listing` (L139-164); `scrapers/parsers/joonggonara.py` L65(검색 결과 가격 고정값 `"가격문의"`); `scrapers/playwright_joonggonara.py` / `enrich_item_async` (L78, L85), `scrapers/joonggonara.py` L137, L144; `engine/metadata.py` 예산 로직(L142-190), `engine/search_flow.py` L235-277
* **우선순위:** Medium
* **신뢰도:** Confirmed (DB 레벨 재현). 엔진 경로는 코드 추적입니다.
* **문제:**
  - 중고나라 검색 결과는 항상 `price="가격문의"`(숫자 0)이고, 상세 보강을 거쳐야 실제 가격(`"35만원"`)이 됩니다. 보강은 플랫폼·키워드·사이클당 10건 예산이라, 한 번 보강된 매물도 다음 사이클에 예산 밖이면 `"가격문의"`로 다시 들어옵니다.
  - `add_listing`은 `old_price != item.price and old_numeric != new_numeric`이면 가격 변동으로 기록하고, `_prefer_non_empty`는 비어 있지 않은 `"가격문의"`로 **실제 가격을 덮어씁니다.**
  - 별도로, postfilter 보강 경로에서는 `matches()`가 이미 `price_numeric=0`을 캐시한 상태에서 보강 결과가 `price_numeric=item.price_numeric`을 그대로 넘깁니다. 그래서 DB에 `price="35만원", price_numeric=0`이 저장됩니다.
* **발생 조건:** 중고나라 키워드에 보강이 활성화된 경우입니다. 즉 키워드 지역 필터 설정, 중고나라에 적용되는 차단 판매자 존재, 또는 `metadata_enrichment_enabled=True` 중 하나이고, 그 뒤 새 글이 올라와 기존 매물이 상위 10건 밖으로 밀리면 발생합니다(보강 예산은 목록 앞에서부터 소모).
* **영향:** 매물마다 "35만원 → 가격문의" 가짜 가격 변동 알림이 나가고(`is_first_run` 이후), `price_history`가 오염되며, 표시 가격이 퇴행합니다. stale `price_numeric=0`은 통계 평균, UI 가격 필터, 즐겨찾기 목표가 도달 판정을 왜곡합니다.
* **근거 (재현):** 동일 `article_id`에 `35만원 → 가격문의 → 35만원 → 가격문의` 순서로 `add_listing`을 호출하자, 2·3·4회차 모두 `price_change`가 반환되고 `price_history` 3행이 쌓였습니다. postfilter 시나리오에서는 `{'price': '35만원', 'price_numeric': 0}`이 저장되었습니다.
* **반증 확인:** 숫자 비교 가드(`old_numeric != new_numeric`)는 포맷 차이(예: `35만원` vs `350,000원`)만 걸러내며, 0과 실제가의 차이는 막지 못합니다. `matches_price`가 가격 0을 통과시키는 것은 문서화된 의도("가격 미상 매물 누락 방지")이므로 버그로 보지 않았습니다.
* **호출/영향 범위:** `search_keyword` → `_enrich_items_with_budget` → `enrich_item_metadata` → `PlaywrightJoonggonaraScraper.enrich_item_async` / `JoonggonaraScraper.enrich_item` → `add_listing` → `send_notifications(is_price_change=True)` → 모든 notifier, `price_history`, 통계 위젯.
* **권장 수정 방향:**
  1. `add_listing`에서 "알 수 없는 가격"(빈 문자열, `가격문의`, `N/A` 등 명시적 placeholder 집합)은 **정보 없음**으로 취급합니다. 기존 실가격을 덮어쓰지 않고 가격 변동으로도 기록하지 않습니다(`무료나눔` 같은 실제 0원과 구분).
  2. 보강 결과에서 `price`를 교체하면 `price_numeric=None`으로 재계산되게 합니다.
  3. 파서 수정 금지 규칙과 충돌하지 않도록 스토리지 계층에서 처리하는 것을 권장합니다.
* **필요한 회귀 테스트:** 위 4회 호출 시퀀스에서 `price_change`는 전부 None, 최종 `price == "35만원"`, `price_history` 0행. postfilter 보강 후 `price_numeric == 350000`. `"1만원" → "무료나눔"`은 여전히 가격 변동으로 기록.

---

### [ISSUE-005] 폴백이 없는 플랫폼에서 메타데이터 보강 시 항목마다 primary 스크래퍼 전체 재기동

* **위치:** `engine/metadata.py` / `enrich_item_metadata` (L116-126); `engine/scrapers.py` / `_ensure_scraper` (L253-262), `initialize_scrapers` (L200-208)
* **우선순위:** Medium
* **신뢰도:** Confirmed (가짜 스크래퍼 재현)
* **문제:** 보강 루프는 `for use_fallback in (False, True)`로 도는데, primary 보강 후에도 seller/location이 비어 있으면 `_ensure_scraper(platform, use_fallback=True)`를 호출합니다. 폴백이 없으면 `initialize_scrapers([platform])`가 실행되고, 이는 **해당 플랫폼의 primary를 닫고 새로 만듭니다.** 그 결과 폴백은 여전히 없으므로 다음 항목에서 같은 일이 반복됩니다.
* **발생 조건:** `scraper_mode=selenium_only`(폴백이 구조적으로 없음), 또는 `playwright_primary`에서 Selenium/Chrome 초기화가 실패한 환경(onefile 배포에 Chrome 미설치 등). 여기에 보강 후에도 metadata가 부족한 경우(중고나라 상세에 지역이 없는 글 등)가 겹쳐야 합니다.
* **영향:** 보강 1건당 브라우저 1회 종료·재기동이 일어납니다(Chrome/Chromium 기동은 수 초). 키워드·플랫폼당 최대 10회이므로 사이클 시간이 급증하고, 봇 탐지에 노출되는 빈도가 늘고, stop 응답성이 나빠집니다(ISSUE-006).
* **근거 (재현):** `selenium_only` 엔진에서 `_create_scraper`를 가짜 스크래퍼로 대체한 뒤, seller/location을 채우지 못하는 보강을 10건 수행하자 **10개 인스턴스가 새로 생성되고 10개가 close**되었습니다.
* **반증 확인:** 검색 경로(`scrape_platform`)는 `fallback_scraper is None`을 먼저 확인하므로 이 문제가 없습니다. 보강 경로에만 이 가드가 빠져 있습니다. 보강 캐시(`_enrichment_cache`)는 같은 `article_id`의 사이클 내 재보강만 막습니다.
* **호출/영향 범위:** `search_keyword` → `_enrich_items_with_budget`(prefilter/postfilter) → `enrich_item_metadata` → `_ensure_scraper` → `initialize_scrapers` → `_close_scraper`/`_create_scraper`/`_start_scraper`.
* **권장 수정 방향:** 보강 루프에서 `use_fallback=True`일 때 `platform not in self.fallback_scrapers`이면 건너뜁니다. `_ensure_scraper(use_fallback=True)`가 primary를 재초기화하지 않도록 역할을 분리합니다.
* **필요한 회귀 테스트:** 폴백 없는 엔진에서 보강 10건 → `_create_scraper` 호출 0회, `initialize_scrapers` 호출 0회.

---

### [ISSUE-006] 모니터링 중지 시 UI 최대 10초 블로킹, 실행 중인 QThread 참조 해제, 중지 후에도 사이클 계속 진행

* **위치:** `gui/main/window_mixins/monitoring.py` / `stop_monitoring` (L60-66); `gui/main/threads.py` / `MonitorThread.stop` (L71-82); `engine/runtime.py` / `stop` (L126-139, 15초 대기); `engine/search_flow.py` / `run_cycle` (L369-389, `self.running` 확인 없음)
* **우선순위:** Medium
* **신뢰도:** Confirmed (UI 블로킹과 스레드 잔존은 재현). 참조 해제 후 동작은 PySide6 격리 실험으로 비정상 종료를 확인했습니다.
* **문제:**
  1. `MonitorThread.stop()`은 UI 스레드에서 `future.result(timeout=5)`로 대기하고, 이어서 `wait(5000)`으로 또 대기합니다. 엔진의 `stop()`은 시작 태스크를 **15초** 기다리므로 5초 안에 끝날 수 없는 구조입니다.
  2. `run_cycle`의 키워드 루프는 `self.running`을 확인하지 않습니다. `_sleep_or_stop(2)`는 stop 이후 즉시 반환하므로, 중지 요청 후에도 **남은 키워드 검색을 연달아 수행**합니다.
  3. `wait(5000)`이 타임아웃되어도 `self.monitor_thread = None`으로 실행 중인 QThread 참조를 버립니다.
* **발생 조건:** 키워드 2개 이상으로 검색 중 중지, 트레이 중지, 설정 저장(자동 재시작), 복원/정리, 앱 종료. 네트워크 장애로 알림 큐가 남아 있으면 drain이 최대 20초, Selenium 검색이 executor에 있으면 `shutdown(wait=True)`가 페이지 로드 타임아웃까지 걸립니다.
* **영향:** 창이 최대 10초 응답 없음. 설정 저장 시 이전 엔진이 정리 중인 상태에서 새 엔진이 시작되어 브라우저 세트가 중복되고 공유 DB에 동시 쓰기가 발생합니다. 앱 종료 시 `quit_app`이 스레드 종료 전에 `self.db.close()`를 호출해 엔진 쓰기가 실패합니다.
* **근거:**
  - 실제 `MonitorThread`에 "cleanup이 느린" 가짜 엔진을 붙여 `stop_monitoring`과 같은 절차(`stop()` → `wait(5000)`)를 실행한 결과: **UI 스레드 10.0초 블로킹**, 이후에도 `isRunning()==True`.
  - PySide6 격리 실험에서 실행 중인 `QThread` 참조를 버린 프로세스는 종료 코드 **127**(비정상), 정상적으로 `wait()`한 대조군은 **0**이었습니다.
* **반증 확인:**
  - `MonitorThread.stop`의 `loop.stop()` 폴백은 run_until_complete를 풀어 줄 뿐이고, 이후 `finally`의 태스크 취소·gather와 `_cleanup_resources`(drain 20초 + scraper close 20초 + executor `wait=True`)가 같은 스레드에서 계속 실행됩니다.
  - `_resources_closed` 플래그는 중복 정리만 막을 뿐, 대기 시간을 줄이지 않습니다.
* **호출/영향 범위:** `toggle_monitoring`, 트레이 `stop_monitoring_requested`, `_apply_settings_after_save`, `quit_app`, `UpdaterMixin`(업데이트 전 중지), `run_cleanup_now`/`restore_selected_backup`(ISSUE-003 수정 후).
* **권장 수정 방향:**
  - 중지를 비동기화합니다: 버튼 비활성화 → `stop_event` 설정 → `finished` 시그널에서 UI 복구와 참조 해제. 스레드 참조는 종료 전까지 유지합니다.
  - `run_cycle`의 키워드 루프와 `search_keyword`의 플랫폼 처리 사이에 `if not self.running: break`를 둡니다.
  - 엔진 `stop()` 대기와 스레드 대기 시간을 일관되게 맞추고, 재시작은 이전 스레드 `finished` 이후에만 수행합니다.
* **필요한 회귀 테스트:** 키워드 3개 + 검색마다 1초 걸리는 가짜 스크래퍼에서 첫 키워드 중 stop → 이후 검색 호출 0회, `stop()` 반환까지 2초 미만. `stop_monitoring()`이 UI 스레드를 200ms 이상 막지 않음. 재시작 시 동시에 살아 있는 엔진은 1개.

---

### [ISSUE-007] 가격 파싱 마이그레이션이 500행 이후 중단되고도 완료로 기록됨

* **위치:** `storage/schema.py` / `_migrate_price_parse_version` (L345-357, price_history는 L360-378)
* **우선순위:** Medium
* **신뢰도:** Confirmed (재현)
* **문제:** 같은 `cursor`로 `SELECT` 결과를 `fetchmany(500)`하면서 그 사이에 `cursor.executemany(UPDATE ...)`를 실행합니다. 이 순간 SELECT 결과 집합이 폐기되어, 두 번째 `fetchmany`는 빈 결과를 반환하고 루프가 끝납니다. 그런데도 마지막에 `price_parse_version=2`로 기록하므로 **다시는 재시도되지 않습니다.** `price_history` 루프도 같은 패턴입니다.
* **발생 조건:** `meta.price_parse_version < 2`이고 listings가 500행을 넘는 DB. 2026-02 이전 버전의 DB이거나, 그런 시점의 백업을 복원한 경우입니다.
* **영향:** 501번째 이후 행의 `price_numeric`이 예전 파서 값(또는 0)으로 영구히 남습니다. 통계와 UI 가격 필터가 틀어지고, 가격 변동 판정에서 `"10만원"(stale 0)` vs `"100,000원"(100000)`처럼 **가짜 가격 변동**이 생길 수 있습니다.
* **근거 (재현):** listings 1200행(`price="10만원"`, `price_numeric=0`) + `price_parse_version=1`로 DB를 재오픈한 결과, **500/1200행만 재계산**되었고 meta는 2로 기록되었습니다.
* **반증 확인:** 이 마이그레이션은 `create_tables()`에서 try/except로 감싸져 있지만 예외가 나지 않으므로 경고조차 남지 않습니다. 테스트는 소량 행으로만 검증합니다.
* **호출/영향 범위:** `DatabaseManager.__init__` → `create_tables` → `_migrate_price_parse_version`. MainWindow, 엔진, 정리 워커, 위젯의 standalone DB 생성 시점마다 실행됩니다(최초 1회만 유효).
* **권장 수정 방향:** id 목록을 먼저 `fetchall()`하거나 UPDATE용 커서를 분리합니다. 이미 잘못 완료 처리된 DB를 위해 `PRICE_PARSE_VERSION`을 3으로 올려 재실행합니다.
* **필요한 회귀 테스트:** 1200행, version 1 → 재오픈 → 1200행 모두 재계산. price_history 1200행도 동일하게 검증.

---

### [ISSUE-008] 엑셀/CSV 내보내기 수식 인젝션 (판매자가 제어하는 제목)

* **위치:** `export_manager.py` / `export_to_csv` (L30-36), `export_to_excel` (L87-89); 호출부 `gui/export/mixins/actions.py` L177, `gui/widgets/stats/mixins/actions.py` L191
* **우선순위:** Medium
* **신뢰도:** Confirmed (재현)
* **문제:** 매물 제목·판매자명·지역은 외부 마켓 사용자가 입력한 값입니다. openpyxl은 `=`로 시작하는 문자열을 **수식 셀**로 저장하고, CSV는 원문을 그대로 기록합니다. Excel로 열면 수식으로 해석됩니다.
* **발생 조건:** `=`, `+`, `-`, `@`로 시작하는 제목의 매물이 수집되고, 사용자가 그 목록을 내보내 Excel로 여는 경우입니다.
* **영향:** `=HYPERLINK(...)` 피싱 링크, 외부 데이터 참조, 구버전 Excel의 DDE 경고 유도 등. 사용자 PC 문맥에서 실행됩니다.
* **근거 (재현):** 제목 `=HYPERLINK("http://example.invalid","클릭")`로 `export_to_excel`을 실행하자 셀 `data_type='f'`였습니다. `export_to_csv`에 `=1+1`을 넣으면 행이 `=1+1,1`로 기록되었습니다.
* **반증 확인:** 내보내기 전 이스케이프·정제 코드가 없습니다(grep). 파서의 제목 정규화는 공백만 처리합니다.
* **권장 수정 방향:** OWASP CSV Injection 권고대로 위험 선행 문자(`= + - @ \t \r`)에 `'`를 붙이고, xlsx에서는 셀을 명시적으로 문자열(`cell.data_type = "s"`)로 지정합니다.
* **필요한 회귀 테스트:** 제목 `=1+1`, `+cmd`, `@SUM(A1)`, `-2+3` → xlsx `data_type == "s"`이고 값이 `'`로 시작. CSV 결과가 `'=1+1`. 일반 제목(`아이폰 15`)은 변형되지 않음.

---

### [ISSUE-009] Windows CLI 모드는 Selector 이벤트 루프를 강제하여 Playwright를 사용할 수 없음

* **위치:** `main.py` / `run_cli` (L58-61); `engine/scrapers.py` / `_probe_playwright_runtime_sync` (L30-44)
* **우선순위:** Medium
* **신뢰도:** Confirmed (probe 재현)
* **문제:** `run_cli`는 Windows에서 `WindowsSelectorEventLoopPolicy`를 설정합니다. Selector 루프는 Windows에서 subprocess를 지원하지 않는데, Playwright는 드라이버를 subprocess로 띄우므로 `NotImplementedError`로 실패합니다. 런타임 probe도 executor 스레드의 `asyncio.run()`에서 같은 정책을 따르므로 "Playwright runtime unavailable"로 판정되고, **기본 엔진(`playwright_primary`)이 CLI에서는 절대 쓰이지 않습니다.** GUI(`MonitorThread`)는 Proactor를 명시해 이 문제가 없습니다.
* **발생 조건:** Windows에서 `python main.py --cli`.
* **영향:** Selenium/Chrome이 있으면 조용히 Selenium으로 강등되고, 없으면 "No scrapers initialized"로 CLI가 즉시 종료됩니다. README는 CLI를 홈서버/백그라운드 용도로 안내합니다.
* **근거 (재현):** 같은 인터프리터에서 정책만 바꿔 probe를 실행했습니다. Proactor는 브라우저 실행 파일 확인 단계까지 진행했고(이 환경은 Chromium 미설치), Selector는 `create_subprocess_exec`에서 `NotImplementedError`로 실패했습니다.
* **반증 확인:** Linux/macOS에서는 이 분기가 실행되지 않으므로 영향이 없습니다. CLAUDE.md의 "비동기 패턴"이 이 설정을 권장하고 있어(문서 불일치, 6장), 의도된 설계로 보이지만 Playwright 도입 이후 맞지 않게 되었습니다.
* **권장 수정 방향:** Windows CLI에서도 Proactor(3.8+ 기본값)를 사용하도록 정책 설정을 제거합니다. 참고로 Python 3.14에서 `asyncio.set_event_loop_policy` 계열은 deprecated입니다(`.venv`는 3.14).
* **필요한 회귀 테스트:** Windows에서 `run_cli` 진입 직후 `asyncio.get_event_loop_policy()`가 Selector가 아님을 확인(엔진은 모킹). 플랫폼 조건부 테스트로 작성합니다.

---

### [ISSUE-010] 데이터 파일 경로가 CWD 기준 — 실행 위치에 따라 다른 DB/설정 사용 또는 시작 실패

* **위치:** `app_settings/constants.py` (`SETTINGS_FILE = "settings.json"`); `models/app_settings.py` L29 (`db_path = "listings.db"`); `main.py` / `setup_logging` (`"notifier.log"`); `backup/manager.py` (`"backup"`); 대조: `updater/constants.py` / `app_storage_root()`(exe 폴더 기준)
* **우선순위:** Medium
* **신뢰도:** 경로 처리는 Confirmed(코드). 사용자 영향은 Likely.
* **문제:** 설정·DB·로그·백업이 모두 CWD 상대 경로입니다. exe를 다른 작업 디렉터리에서 실행하면 빈 설정·빈 DB가 새로 생성됩니다. 작업 스케줄러의 기본 시작 위치(`C:\Windows\System32`)처럼 쓰기 권한이 없는 CWD에서는 `RotatingFileHandler("notifier.log")`가 `PermissionError`를 내고, `setup_logging()`이 예외 처리 밖에 있어 **GUI가 뜨기 전에 종료**됩니다(windowed exe라 사용자에게 아무 메시지도 보이지 않음).
* **발생 조건:** 터미널에서 다른 폴더를 기준으로 실행, "시작 위치"가 다른 바로가기, 작업 스케줄러 자동 실행.
* **영향:** 사용자는 "키워드/매물이 사라졌다"고 인식하고(데이터가 다른 위치에 생성됨), 자동 실행이 조용히 실패합니다. 업데이터는 exe 폴더를, 앱은 CWD를 기준으로 삼아 서로 어긋납니다.
* **반증 확인:** 업데이터는 헬퍼와 재실행 모두 부모 CWD를 상속하므로(`subprocess.Popen`에 `cwd` 없음), **업데이트 자체로 경로가 바뀌지는 않습니다.** 탐색기 더블클릭은 exe 폴더가 CWD라 정상 동작합니다. 따라서 Critical/High가 아닌 Medium으로 분류했습니다.
* **권장 수정 방향:** 앱 전체에서 `app_storage_root()`(또는 `%LOCALAPPDATA%\UsedMarketNotifier`)를 단일 기준으로 삼아 절대 경로를 만듭니다. 기존 CWD 데이터는 1회 마이그레이션합니다. `setup_logging` 실패 시 로그 없이도 기동하도록 방어합니다.
* **필요한 회귀 테스트:** CWD를 임시 폴더로 바꾼 상태에서 `SettingsManager()`/`DatabaseManager` 기본 경로가 exe/앱 루트 기준인지 확인. CWD를 읽기 전용 폴더로 두고 `setup_logging()`이 예외를 던지지 않는지 확인.

---

### [ISSUE-011] 명시적 판매 상태(`sold`)가 다음 사이클에 제목 기반 `for_sale`로 되돌아감

* **위치:** `storage/listings.py` / `add_listing` (L128-136), `detect_sale_status` (L312-319)
* **우선순위:** Low
* **신뢰도:** Confirmed (DB 레벨 재현). 실사용 빈도는 Likely-Low.
* **문제:** `explicit_status`가 없으면 `detect_sale_status(title)`을 쓰는데, 이 함수는 결코 None을 반환하지 않습니다(기본 `for_sale`). 그래서 `new_status = detected_status or old_status`의 `old_status` 분기에 도달하지 않고, 상세 API로 확인된 `sold`/`reserved`가 상태 정보 없는 검색 카드 한 번에 덮어써집니다.
* **발생 조건:** 번개장터 상세 보강으로 `sold`가 기록된 뒤, 판매완료 매물이 검색 결과에 남아 있고 다음 사이클에 보강되지 않을 때.
* **영향:** `sale_status_history`에 `for_sale → sold → for_sale` 왕복 기록이 남고, 목록/통계의 판매 상태가 부정확해집니다.
* **근거 (재현):** `sale_status=None → "SOLD_OUT" → None` 순서로 `add_listing` → 최종 `for_sale`, 이력 `[('for_sale','sold'), ('sold','for_sale')]`.
* **권장 수정 방향:** 명시 상태가 없고 제목에도 판매 상태 단서가 없으면 기존 상태를 유지합니다(`detect_sale_status`가 "단서 없음"을 None으로 반환하도록).
* **필요한 회귀 테스트:** 위 시퀀스 → 최종 `sold`, 이력 1행. 제목에 `판매완료`가 포함되면 여전히 `sold`로 전이.

---

## 5. Potential Functional Gaps

| 구분 | 항목 | 근거 |
|------|------|------|
| **Confirmed Gap** | **알림 폭주 안전장치 부재**: 사이클/키워드당 알림 상한, 다이제스트, 채널별 발송 간격 제어가 없습니다. ISSUE-002 같은 결함이 그대로 외부 채널 스팸으로 이어집니다. | `engine/notification_sections/queue.py`는 20건 이상 백로그 경고만 남김 |
| **Confirmed Gap** | **정리 기준이 `created_at`(최초 발견 시각)**: 여전히 검색 결과에 있는 매물도 N일이 지나면 삭제되고, 다음 사이클에 "새 매물"로 재등록됩니다. 시작 시 자동 정리는 첫 사이클 억제로 가려지지만, 모니터링 중 수동 정리(ISSUE-003)에서는 재알림이 발생합니다. `last_seen_at` 개념이 없습니다. | `storage/maintenance.py` L84-86 |
| **Confirmed Gap** | **알림 자격 증명 평문 저장**: Telegram 토큰·Discord/Slack 웹훅이 `settings.json` 평문으로 저장되고 백업 ZIP에도 그대로 들어갑니다. `cryptography` 의존성은 업데이트 서명 검증에만 쓰입니다. Windows DPAPI 등 OS 보안 저장소는 사용하지 않습니다. | `app_settings/mixins/serialization.py`, `backup/mixins/creator.py` |
| **Likely Gap** | **단일 인스턴스 보장 없음**: 자동 시작과 수동 실행이 겹치면 두 엔진이 같은 DB에 쓰고 알림이 중복되며, 브라우저 세트도 2배가 됩니다. | `QLockFile`/`QLocalServer`/뮤텍스 사용 없음(grep) |
| **Likely Gap** | **설정 저장 비원자성**: `open(path, 'w')` 후 `json.dump`하므로 쓰기 도중 강제 종료/정전 시 파일이 잘립니다. 로드 시 격리 + 백업 복구 경로가 있어 완전 유실은 아니지만, 마지막 백업 이후 변경분은 잃습니다. 임시 파일 + `os.replace`로 해결할 수 있습니다. | `app_settings/manager.py` L66-75 |
| **Likely Gap** | **폴백 스크래퍼 즉시 생성**: `playwright_primary`에서 플랫폼마다 Playwright 브라우저와 Selenium Chrome 드라이버를 모두 시작 시점에 띄웁니다(Selenium은 생성자에서 드라이버 생성). 최대 6개 브라우저 프로세스가 상주합니다. 폴백은 필요할 때 생성하는 편이 자원 면에서 유리합니다. | `engine/scrapers.py` L207-222, `scrapers/selenium_base.py` L67 |
| **추정** | `custom_interval`과 `search_stats`가 키워드 **텍스트**만 키로 씁니다. 같은 텍스트에 플랫폼·지역이 다른 키워드 2개가 간격 판정을 공유합니다. | `engine/search_flow.py` L373-374 |
| **추정** | `asyncio.set_event_loop_policy`/`Windows*EventLoopPolicy`는 Python 3.14에서 deprecated이며(`.venv`=3.14), 향후 버전에서 제거되면 GUI 스레드 초기화가 깨질 수 있습니다. 현재 버그는 아닙니다. | `gui/main/threads.py` L27-30, `main.py` L58-61 |
| **추정** | 첫 실행 억제 정책 때문에 앱이 꺼져 있던 동안 올라온 매물은 재시작 첫 사이클에서 알림 없이 저장됩니다. README에 명시된 의도이지만, "놓친 매물 요약" 같은 보완 기능은 없습니다. | README "첫 검색 사이클 폭풍 알림 방지" |

---

## 6. Documentation Mismatches

| 문서 | 기술 내용 | 실제 구현 |
|------|-----------|-----------|
| CLAUDE.md (2026-04 Stabilization) | "backup restore stops monitoring and exits after restore to avoid stale DB handles" | Fluent 셸에서는 모니터링을 중지하지 않고(ISSUE-003), MainWindow의 DB 연결도 열린 채 파일을 덮어씁니다(ISSUE-001). |
| README "안전한 ZIP 백업 & 복원" | 백업/복원이 안전하다고 안내 | ZIP 경로 검증은 안전하지만 복원 자체가 열린 DB를 손상시킵니다. |
| README 기능 요약·"폭풍 알림 방지" | 첫 사이클에 기존 매물이 한꺼번에 알림으로 가는 현상을 방지 | 엔진 시작 시 1회만 적용됩니다. 모니터링 중 추가한 키워드는 기존 매물 전체를 알림으로 보냅니다(ISSUE-002). |
| README "판매자 차단 관리" | 차단 판매자 관리 기능 | 설정 > 차단 관리 목록은 항상 비어 있고 해제가 실패합니다(ISSUE-003). |
| CLAUDE.md "비동기 패턴" | Windows에서 `WindowsSelectorEventLoopPolicy` 설정을 권장(✅) | 이 설정은 Playwright를 불가능하게 만듭니다(ISSUE-009). GUI 스레드는 Proactor를 씁니다. |
| README 배지/본문, CLAUDE.md | 테스트 수 156(배지), 144(본문 2곳), 151(CLAUDE 2026-09), 91(CLAUDE 2026-03) | 실제 `Ran 162 tests`. |
| CLAUDE.md "코딩 컨벤션" 예시 | 퍼지 중복: "최근 24시간 내 유사 제목" | 실제는 최근 **3일**, **같은 가격 문자열** 후보 20건 한정입니다(`storage/listings.py` L258-264). |
| CLAUDE.md 상단 섹션 | `PyQt6`, `pyqtSignal`, `QThread` 예제와 Catppuccin QSS 적용 | 2026-09 섹션에서 PySide6/Fluent로 대체되었다고 명시되어 있으나, 상단 본문은 그대로입니다. 문서 내부에서 서로 충돌합니다. |
| 저장소 파일명 | 에이전트 지침이 `CLAUDE.md`를 참조 | git에는 소문자 `claude.md`로 추적됩니다. Windows에서는 문제없지만 Linux/macOS 같은 대소문자 구분 파일시스템에서는 `CLAUDE.md`로 찾을 수 없습니다. |
| 요청 문서 | `AGENTS.md` | 저장소에 없습니다. |

---

## 7. Recommended Fix Plan

### Phase 1 — Immediate

데이터 손상, 주요 기능 실패, 심각한 동시성 문제를 다룹니다.

1. **ISSUE-001 복원 재설계**: SQLite backup API로 열린 연결에 복원하거나, 다음 시작 시 연결을 열기 전에 적용하는 "보류 복원"으로 전환합니다. `.pre_restore`도 backup API로 생성합니다.
2. **ISSUE-003 host 해석 수정**: `SettingsPage`에 MainWindow host를 명시적으로 주입(또는 `self.window()`)하고, host가 없으면 복원/정리를 거부합니다. 차단 판매자 탭 DB 접근을 복구합니다.
3. **ISSUE-002 알림 기준선**: `(keyword, platform)` 단위의 영속 기준선을 도입하고, 사이클당 알림 상한을 안전장치로 추가합니다.

### Phase 2 — Stability

예외 처리, 입력 검증, transaction, retry, 상태 관리, OS 호환성을 다룹니다.

4. **ISSUE-004** 알 수 없는 가격 placeholder가 실가격을 덮어쓰거나 가격 변동으로 기록되지 않게 하고, 보강 시 `price_numeric`을 재계산합니다.
5. **ISSUE-006** 비동기 중지(시그널 기반), `run_cycle`/`search_keyword`에 중지 확인, 스레드 참조 유지, 재시작 직렬화를 적용합니다.
6. **ISSUE-005** 보강 경로에서 폴백이 없으면 건너뛰도록 해 primary 재초기화를 막습니다.
7. **ISSUE-007** 마이그레이션 커서를 분리하고 `PRICE_PARSE_VERSION=3`으로 재실행합니다.
8. **ISSUE-008** 내보내기 셀 값을 정제합니다.
9. **ISSUE-009** Windows CLI에서 Selector 정책 설정을 제거합니다.
10. **ISSUE-010** 앱 데이터 루트를 단일화하고 `setup_logging` 실패를 방어합니다.
11. 설정 파일 원자적 저장(임시 파일 + `os.replace`), **ISSUE-011** 판매 상태 유지 규칙을 적용합니다.

### Phase 3 — Structural

구조 개선, 테스트 가능성, 책임 분리를 다룹니다.

12. GUI mixin과 host 사이의 암묵적 `getattr(parent, ...)` 계약을 명시적 인터페이스(Protocol)로 바꾸고, 실패 시 조용히 넘어가지 않게 합니다(현재 `except Exception: pass`가 ISSUE-003을 가렸습니다).
13. 정리 기준을 `last_seen_at` 기반으로 바꾸고(스키마는 컬럼 추가만 하는 방식으로 기존 호환 유지), "놓친 매물 요약" 알림을 검토합니다.
14. 단일 인스턴스 락, 폴백 스크래퍼 지연 생성, 알림 자격 증명의 OS 보안 저장소(DPAPI) 이전을 적용합니다.
15. 오프스크린 `MainWindow` 기반 통합 테스트 계층을 추가해, 셸 구조 변경 시 host/시그널 연결 회귀를 자동 검출합니다.

---

## 8. Test Recommendations

### Unit

- **가격 placeholder (ISSUE-004):** `add_listing("35만원")` → `add_listing("가격문의")` → `price_change is None`, 저장 가격 `"35만원"`, `price_history` 0행. `"10,000원" → "무료나눔"`은 `price_change` 반환.
- **보강 price_numeric (ISSUE-004):** `Item(price="가격문의")`에 `parse_price()` 후 보강 결과(`"35만원"`)를 저장 → `price_numeric == 350000`.
- **판매 상태 유지 (ISSUE-011):** `None → "SOLD_OUT" → None` → `sold`, 이력 1행. 제목 `"[판매완료] 맥북"` → `sold`.
- **마이그레이션 (ISSUE-007):** listings·price_history 각 1200행, version 1 → 재오픈 후 전 행 재계산, version 기록.
- **내보내기 정제 (ISSUE-008):** `=1+1`, `+x`, `-2`, `@A1`, `\t=1` → 문자열 셀이고 `'` 접두. 일반 문자열은 불변.
- **경로 (ISSUE-010):** CWD를 임시 폴더로 바꾼 상태에서 기본 설정/DB 경로가 앱 루트 기준.

### Integration

- **복원 (ISSUE-001):** 열린 `DatabaseManager` + WAL 미체크포인트 300행 → 복원 → close/reopen → `integrity_check == ok`, 행 수 == 백업 시점. 복원 직후 같은 연결로 조회해도 백업 내용이 보여야 합니다(backup API 방식일 때).
- **기준선 (ISSUE-002):** 가짜 스크래퍼 엔진에서 (a) 사이클 2회 → 키워드 추가 → 3회차 알림 0, 4회차 신규 1건만. (b) 1회차 플랫폼 예외 → 2회차 성공 → 알림 0. (c) 엔진 교체 후 새로 등장한 매물 1건은 알림 1건.
- **보강 재초기화 (ISSUE-005):** 폴백 없는 엔진에서 보강 10건 → `_create_scraper` 0회.
- **정리 재알림:** `created_at`을 40일 전으로 조작한 매물이 검색 결과에 계속 있을 때, 정리 후 다음 사이클에서 알림이 가지 않아야 합니다(기준선/`last_seen_at` 도입 후).

### End-to-End (오프스크린 GUI, 격리된 CWD)

- `MainWindow` 생성 → 설정 페이지 host 해석이 MainWindow → 모니터링(가짜 엔진) 실행 중 "선택 백업 복원" → `stop_monitoring` 호출 → 복원 후 DB 무결성 확인.
- 차단 판매자 추가(`add_seller_filter`) → 설정 > 차단 관리 테이블 1행 → 해제 → 0행, 다음 사이클에서 해당 판매자 매물 수집.
- `USED_NOTIFIER_GUI_SMOKE=1 python -m gui.app` 스모크에 설정 페이지 host 검증 단계를 추가합니다.

### Concurrency

- **중지 응답성 (ISSUE-006):** 키워드 3개, 검색당 1초 가짜 스크래퍼 → 첫 키워드 중 stop → 추가 검색 0회, `engine.stop()` 2초 이내, `stop_monitoring()` UI 블로킹 200ms 미만.
- **재시작 직렬화:** `_apply_settings_after_save`를 연속 3회 호출 → 동시에 살아 있는 `MonitorThread` 최대 1개, 이전 스레드 `finished` 이후에만 새 스레드 시작.
- **공유 DB:** 엔진 스레드의 `add_listing` 루프와 UI 스레드의 `get_listings_paginated` 동시 실행(1000회) → 예외 0, 락 대기 최대값 기록.

### Regression

- 이번 재현 스크립트 7종(복원 WAL, 키워드 추가 폭주, 가격 왕복, stale price_numeric, 상태 역전, 마이그레이션 500행, 보강 재초기화)을 `tests/`의 네트워크 없는 회귀 테스트로 옮깁니다.
- `FluentChromeContractTest`와 같은 방식으로 "settings mixin이 host 속성을 찾는다"는 계약 테스트를 추가합니다.

### Platform-specific

- **Windows:** `run_cli`의 이벤트 루프가 Proactor인지 확인(ISSUE-009). 읽기 전용 CWD에서 `setup_logging` 방어 확인(ISSUE-010). 열린 SQLite 파일 덮어쓰기가 차단되지 않는다는 전제를 테스트로 고정(ISSUE-001 회귀 방지).
- **Linux/macOS:** 대소문자 구분 파일시스템에서 `claude.md`/`CLAUDE.md` 참조 확인. CLI 모드 Playwright 초기화 스모크(Chromium 설치 환경).

---

## 9. Final Assessment

| 항목 | 평가 | 근거 |
|------|------|------|
| Functional Correctness | **Needs Work** | 핵심 검색/저장/알림 흐름은 동작하지만, 키워드 추가 시 알림 폭주(ISSUE-002), 가짜 가격 변동(ISSUE-004), 차단 해제 불능(ISSUE-003)이 재현됩니다. |
| Runtime Stability | **Needs Work** | 중지 시 UI 10초 블로킹과 스레드 잔존(ISSUE-006), 보강 중 브라우저 재기동 반복(ISSUE-005)이 있습니다. 엔진 루프의 오류 격리, 백오프, 재시도 자체는 견고합니다. |
| Data Integrity | **High Risk** | 복원 시 DB 손상이 재현되고(ISSUE-001), 레거시 마이그레이션이 조기 종료되며(ISSUE-007), `price_history`가 오염됩니다(ISSUE-004). 쓰기 경로의 락과 `(platform, article_id)` UNIQUE, normalized_url 보조 키는 잘 되어 있습니다. |
| Error Resilience | **Acceptable** | 알림 채널별 재시도·429 처리, 설정 손상 격리·복구, 업데이트 서명 검증과 롤백은 좋습니다. 다만 GUI mixin의 광범위한 `except Exception: pass`가 ISSUE-003 같은 기능 실패를 숨깁니다. |
| Cross-platform Robustness | **Needs Work** | CWD 의존 경로(ISSUE-010), Windows CLI 이벤트 루프(ISSUE-009), deprecated 루프 정책 API 의존, 대소문자 파일명이 걸립니다. |
| Test Confidence | **Acceptable** | 162개 테스트가 통과하고 파서·정책 단위 커버리지가 넓습니다. 반면 열린 연결 상태의 복원, 모니터링 중 키워드 변경, Fluent 셸의 host 연결, 대량 행 마이그레이션처럼 이번에 발견된 결함이 있는 경로는 테스트되지 않습니다. |

### 실제로 먼저 수정할 문제 3개

1. **ISSUE-001 — 백업 복원 DB 손상.** 사용자가 데이터를 지키려고 쓰는 기능이 오히려 DB를 파괴하거나 조용히 무효화됩니다. SQLite backup API 기반 복원(또는 시작 전 보류 복원)으로 교체해야 합니다.
2. **ISSUE-003 — SettingsPage host 해석.** 한 줄 수준의 수정(`window()` 또는 host 주입)으로 복원/정리 전 모니터링 중지와 차단 판매자 관리가 함께 복구되고, ISSUE-001의 위험도 줄어듭니다.
3. **ISSUE-002 — 알림 기준선.** 가장 흔한 사용 흐름(모니터링 중 키워드 추가)에서 외부 채널 스팸이 발생하고, 설정 저장 시에는 신규 매물 알림이 누락됩니다. `(keyword, platform)` 단위 기준선과 알림 상한으로 해결합니다.
