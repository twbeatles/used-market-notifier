# Implementation Plan: 감사 결과 전체 수정 (Audit Remediation 2026-09)

**Branch**: `001-audit-remediation` | **Date**: 2026-09-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-audit-remediation/spec.md`

## Summary

`PROJECT_AUDIT.md`(2026-09-28)의 ISSUE-001~011, 기능 갭 7건, 문서 불일치를 수정한다. 주요 설계는 다음과 같다.

- **복원**: 파일 복사 대신 SQLite online backup API로 복원한다(열린 WAL 연결과 안전하게 공존).
- **알림**: 새 테이블 기반의 `(keyword 서명, platform)` 영속 기준선과 사이클 알림 상한을 도입한다.
- **설정 화면**: host 해석을 `window()` 기반으로 바꾸고 명시적 host 계약을 둔다.
- **모니터링 중지**: 비동기 중지 요청과 finished 시그널 기반의 스레드 수명 관리로 바꾼다.
- **가격·판매 상태**: 저장 계층에서 교정하고, 스크래퍼 파싱 코드는 건드리지 않는다.
- **런타임 보강**: 폴백 스크래퍼 지연 생성·재시도 쿨다운, 프로세스 시작 시 앱 루트로 chdir, 단일 인스턴스 `QLockFile`, 원자적 설정 저장, Windows DPAPI 비밀값 보호, 내보내기 셀 정제, deprecated asyncio 정책 API 제거.

## Technical Context

**Language/Version**: Python 3.10+ (pyright baseline 3.10, 로컬 `.venv`는 3.14)

**Primary Dependencies**: PySide6, PySide6-Fluent-Widgets, playwright, selenium, aiohttp, openpyxl, cryptography(업데이터 전용). 신규 의존성은 없다(DPAPI는 `ctypes`).

**Storage**: SQLite(`listings.db`, WAL) + JSON(`settings.json`) + ZIP 백업

**Testing**: `python -m unittest discover -s tests -q` (network-free), 오프스크린 Qt(`QT_QPA_PLATFORM=offscreen`)

**Target Platform**: Windows 10/11 우선(onefile exe). 소스 실행은 Linux/macOS도 지원한다.

**Project Type**: desktop-app (+ CLI 모드)

**Performance Goals**: 중지 요청 시 UI 블로킹 < 0.2초. 보강 시 브라우저 재생성 0회.

**Constraints**: 기존 테이블 구조 변경 금지(새 테이블만 추가). 스크래퍼 파싱 로직과 `stealth.py`는 수정 금지. 기존 설정 JSON 역호환 유지. legacy import facade 유지.

**Scale/Scope**: 약 30개 모듈 수정, 신규 모듈 3개(`app_paths.py`, `app_settings/secrets.py`, `storage/baselines.py`), 회귀 테스트 약 12개 파일

## Constitution Check

`.specify/memory/constitution.md`는 템플릿 상태(원칙 미정의)이다. 대신 CLAUDE.md의 수정 제약을 게이트로 사용한다.

| 게이트 | 결과 |
|--------|------|
| 스크래퍼 파싱 로직 수정 금지 | PASS — 가격/상태 교정은 `storage/listings.py`, `engine/metadata.py`에서 처리한다. 스크래퍼 파일은 수정하지 않는다. |
| `stealth.py` 수정 금지 | PASS — 변경하지 않는다. |
| 기존 DB 테이블 구조 변경 금지 | PASS — `search_baselines`, `listing_last_seen` 새 테이블만 추가한다. 기존 테이블 컬럼은 불변이다. |
| JSON 직렬화 역호환(주의 영역) | PASS — 평문 비밀값은 그대로 읽는다. `dpapi:v1:` 접두 값만 복호화한다. 비Windows는 평문을 유지한다. |
| PyQt/PySide 시그널: UI 업데이트는 메인 스레드에서만 | PASS — 중지 완료 처리는 `QThread.finished`(queued) 슬롯에서 수행한다. |
| MonitorEngine 비동기 흐름(주의 영역) | PASS — 중지 확인 지점 추가와 stop 대기 조정만 한다. 기존 콜백 시그니처는 유지한다. |

Post-design 재평가: 동일하게 PASS(아래 설계는 위 게이트 밖으로 나가지 않는다).

## Project Structure

### Documentation (this feature)

```text
specs/001-audit-remediation/
├── spec.md
├── plan.md              # 이 파일
├── research.md          # 설계 결정 근거
├── data-model.md        # 신규 테이블, 기준선 서명, 가격 규칙
├── quickstart.md        # 검증 절차
├── contracts/
│   ├── settings-host.md # SettingsPage ↔ MainWindow host 계약
│   └── restore-and-stop.md # 복원/중지 동작 계약
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks 산출물
```

### Source Code (repository root)

```text
app_paths.py                         # [NEW] 앱 루트 해석 + chdir
main.py                              # 앱 루트 chdir, 로깅 방어, CLI 루프 정책 제거
app_settings/
├── manager.py                       # 원자적 save
├── secrets.py                       # [NEW] DPAPI protect/unprotect
└── mixins/serialization.py, deserialization.py  # 비밀값 암복호화
backup/mixins/restorer.py            # backup API 복원, pre_restore 스냅샷
storage/
├── baselines.py                     # [NEW] SearchBaselineMixin, ListingSeenMixin
├── database.py                      # mixin 조립
├── schema.py                        # 새 테이블, 마이그레이션 커서 수정, PRICE_PARSE_VERSION=3
├── listings.py                      # 가격 placeholder, 판매 상태 유지
└── maintenance.py                   # last_seen 기반 정리
price_utils.py                       # is_unknown_price_text
models/item.py                       # notification_suppressed 필드
engine/
├── monitor.py                       # suppress_initial_notifications, 상한, 상태 필드
├── search_flow.py                   # 기준선·상한·중지 확인·간격 식별자·last_seen 기록
├── metadata.py                      # 폴백 부재 skip, price_numeric 재계산
├── scrapers.py                      # 폴백 지연 생성·쿨다운, 폴백만 재생성
└── runtime.py                       # stop 대기 조정
export_manager.py                    # 셀 정제
gui/
├── app.py                           # QLockFile 단일 인스턴스
├── main/threads.py                  # request_stop, Proactor 루프 직접 생성
├── main/window_mixins/monitoring.py # 비동기 stop, 재시작 직렬화, 억제 트레이
├── main/window_mixins/lifecycle.py  # 종료 시 스레드 대기 후 DB close
├── main/window_mixins/updater.py    # 업데이트 전 대기 stop
├── settings_panels/host.py          # [NEW] resolve_settings_host
├── settings_panels/mixins/maintenance.py, seller.py
├── settings_panels/dialog.py, pages/settings_page.py  # _get_parent_db → host.db
└── widgets/keyword/widget.py        # (keywords_changed 유지, 엔진이 기준선으로 처리)
tests/                               # 신규 회귀 테스트
README.md, CLAUDE.md(대소문자 정정), AGENTS.md(신규), PROJECT_AUDIT.md(조치 상태)
```

**Structure Decision**: 기존 단일 프로젝트 구조와 mixin 분할 관례를 따른다. 새 책임은 기존 패키지 내 새 모듈로 추가한다.

## Design Notes (핵심 결정 요약 — 근거는 research.md)

1. **복원**: 임시 추출한 DB를 `sqlite3.connect(temp).backup(dst)`로 `db_path`의 새 연결에 복사한다. WAL 인지 경로라 다른 열린 연결과 공존하며, 페이지 크기 불일치 등 실패 시 현재 DB는 불변이다. `.pre_restore`도 backup API로 만든다. 복원 전 `PRAGMA integrity_check`로 백업 DB를 검증한다.
2. **기준선**: 서명 = `keyword|location|min|max|sorted(exclude)`(소문자·공백 정규화). 검색이 오류 없이 끝나면(0건 포함) 기준선을 기록한다. 기준선이 없던 검색의 신규 매물은 `notification_suppressed=True`로 저장만 한다.
3. **첫 실행 억제**: `MonitorEngine(..., suppress_initial_notifications=True)`가 기본값이다. MainWindow는 프로세스 내 두 번째 이후 시작부터 False를 전달한다.
4. **상한**: `NOTIFICATION_BURST_LIMIT = 15`(키워드·플랫폼·사이클). 초과분은 사이클 처리 끝에 `_send_system_message`로 요약한다(정책 준수).
5. **중지**: `MonitorThread.request_stop()`은 non-blocking이다(`engine.running=False` + 루프에 `stop_event.set` 예약). `stop(timeout)`은 대기형으로 남긴다(종료/복원/업데이트용). 창은 중지 중인 스레드를 `_stopping_threads`에 보관하고 finished에서 해제하며, 대기 중 시작 요청은 `_pending_start`로 처리한다.
6. **폴백 지연 생성**: `initialize_scrapers`는 첫 성공 엔진만 primary로 만들고 나머지 엔진 순서를 `_fallback_candidates[platform]`에 둔다. `_ensure_scraper(use_fallback=True)`에서 필요할 때 생성하고, 실패 시 600초 쿨다운을 둔다. 폴백이 unhealthy이면 폴백만 재생성한다.
7. **경로**: `main()`의 첫 동작으로 `app_paths.ensure_app_root_cwd()`를 호출한다. frozen은 exe 폴더, 소스는 `main.py` 폴더 기준이다.
8. **DPAPI**: `CryptProtectData`/`CryptUnprotectData`(ctypes, 고정 entropy)를 쓴다. 직렬화 시 `token`/`webhook_url`만 보호한다(`chat_id`는 비밀 아님). 복호화 실패 시 값을 비우고 `load_recovery_state["secret_decrypt_failed"]`에 기록해 시작 안내를 띄운다.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 새 테이블 2개 추가 | 기준선·마지막 확인 시각의 영속화 | 기존 `listings`에 컬럼 추가는 "기존 테이블 구조 변경 금지"에 저촉. `search_stats` 재사용은 실패 검색도 기록되어 성공 기준선 판별 불가 |
| 폴백 지연 생성으로 스크래퍼 수명 로직 변경 | 자원 낭비·재기동 반복 제거 | 보강 경로 가드만 추가하면 ISSUE-005는 해결되나 브라우저 6개 상주 갭이 남음 |
