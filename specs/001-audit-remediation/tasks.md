# Tasks: 감사 결과 전체 수정 (Audit Remediation 2026-09)

**Input**: Design documents from `/specs/001-audit-remediation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 포함한다(spec SC-010: 결함 재현 시나리오를 회귀 테스트로 포함). 테스트는 네트워크 없이 `tests/`에 추가한다.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [x] T001 기준 테스트 스위트 통과 확인(`python -m unittest discover -s tests -q`, 162 OK)

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T002 [P] 가격 미상 판별 함수 `is_unknown_price_text()` 추가 in price_utils.py
- [x] T003 [P] `Item.notification_suppressed` 필드(compare/repr 제외) 추가 in models/item.py
- [x] T004 `search_baselines`, `listing_last_seen` 테이블 생성을 schema에 추가 in storage/schema.py
- [x] T005 `SearchBaselineMixin`(서명 생성, has/establish), `ListingSeenMixin`(touch) 구현 in storage/baselines.py 및 DatabaseManager 조립 in storage/database.py

**Checkpoint**: 새 테이블·헬퍼 준비 완료

## Phase 3: User Story 1 - 백업 복원이 데이터를 망가뜨리지 않는다 (P1) 🎯 MVP

**Goal**: 열린 WAL DB 위에서도 일관된 복원과 완전한 pre_restore 사본
**Independent Test**: tests/test_restore_live_db.py

- [x] T006 [P] [US1] 열린 연결 + WAL 행 상태 복원 회귀 테스트 작성 in tests/test_restore_live_db.py
- [x] T007 [US1] backup API 기반 복원·무결성 검증·pre_restore 스냅샷 구현 in backup/mixins/restorer.py

## Phase 4: User Story 2 - 알림은 실제로 새로 올라온 매물에만 온다 (P1)

**Goal**: (서명, 플랫폼) 영속 기준선, 프로세스 첫 엔진만 첫 사이클 억제, 사이클 알림 상한
**Independent Test**: tests/test_notification_baseline.py

- [x] T008 [P] [US2] 키워드 추가/첫 성공 기준선/재시작 알림/상한 회귀 테스트 in tests/test_notification_baseline.py
- [x] T009 [US2] `suppress_initial_notifications` 인자, `NOTIFICATION_BURST_LIMIT` 추가 in engine/monitor.py
- [x] T010 [US2] search_keyword에 기준선 판정·억제 표시·상한·요약 알림·기준선 확정 구현 in engine/search_flow.py
- [x] T011 [US2] 트레이 알림을 `item.notification_suppressed` 기준으로 판단 in gui/main/window_mixins/monitoring.py

## Phase 5: User Story 3 - 설정 화면 유지보수·차단 관리 동작 (P1)

**Goal**: host 해석 수정, 복원/정리 전 대기형 중지, 차단 판매자 조회/해제
**Independent Test**: tests/test_settings_host.py

- [x] T012 [P] [US3] 오프스크린 MainWindow host 해석/차단 목록/복원 전 중지 테스트 in tests/test_settings_host.py
- [x] T013 [US3] `resolve_settings_host()`, `resolve_host_db()` 구현 in gui/settings_panels/host.py
- [x] T014 [US3] 복원·정리·정리 후 새로고침을 host 계약으로 변경 in gui/settings_panels/mixins/maintenance.py
- [x] T015 [US3] `_get_parent_db`를 host 기반으로 변경 in gui/pages/settings_page.py 및 gui/settings_panels/dialog.py
- [x] T016 [US3] 차단 목록 조회 실패 시 사용자 표시 개선 in gui/settings_panels/mixins/seller.py

## Phase 6: User Story 4 - 가격·판매 상태 기록 정확성 (P2)

**Goal**: 가격 placeholder 왕복 차단, 보강 price_numeric 재계산, 판매 상태 유지, 마이그레이션 전 행 처리
**Independent Test**: tests/test_listing_price_status_rules.py, tests/test_price_migration_batches.py

- [x] T017 [P] [US4] 가격/상태 규칙 회귀 테스트 in tests/test_listing_price_status_rules.py
- [x] T018 [P] [US4] 1200행 마이그레이션 회귀 테스트 in tests/test_price_migration_batches.py (기존 tests/test_price_migration.py 유지)
- [x] T019 [US4] add_listing 가격 규칙·판매 상태 유지 구현 in storage/listings.py
- [x] T020 [US4] 마이그레이션 커서 분리 + PRICE_PARSE_VERSION=3 in storage/schema.py, storage/database.py
- [x] T021 [US4] 보강 결과 가격 텍스트 변경 시 price_numeric 재계산 in engine/metadata.py

## Phase 7: User Story 5 - 모니터링 중지·재시작 빠르고 안전 (P2)

**Goal**: 비블로킹 중지, 중지 확인 지점, 스레드 수명 유지, 재시작 직렬화, 종료/업데이트 시 대기
**Independent Test**: tests/test_monitor_stop.py

- [x] T022 [P] [US5] 중지 후 추가 검색 0회, request_stop 비블로킹, 재시작 직렬화 테스트 in tests/test_monitor_stop.py
- [x] T023 [US5] run_cycle/search_keyword 중지 확인 지점 + `request_stop()` 엔진 헬퍼 in engine/search_flow.py, engine/runtime.py
- [x] T024 [US5] `request_stop()`/`stop(timeout)` 및 Proactor 루프 직접 생성 in gui/main/threads.py
- [x] T025 [US5] 비동기 stop·stopping 상태·pending_start·`is_monitoring_active`·대기형 stop 구현 in gui/main/window_mixins/monitoring.py
- [x] T026 [US5] 종료 시 스레드 대기 후 DB close in gui/main/window_mixins/lifecycle.py, 업데이트 전 대기 stop in gui/main/window_mixins/updater.py

## Phase 8: User Story 6 - 브라우저 자원 낭비 제거 (P2)

**Goal**: 보강 시 폴백 부재 skip, 폴백 지연 생성·쿨다운·폴백만 재생성
**Independent Test**: tests/test_fallback_lifecycle.py

- [x] T027 [P] [US6] 보강 재생성 0회·지연 생성·쿨다운 테스트 in tests/test_fallback_lifecycle.py
- [x] T028 [US6] 폴백 후보 기록·지연 생성·쿨다운·폴백 단독 재생성 in engine/scrapers.py
- [x] T029 [US6] 검색 경로 폴백 가용성 판정을 `_has_fallback_option` 기반으로 변경 in engine/search_flow.py
- [x] T030 [US6] 보강 루프에서 폴백 부재 시 skip in engine/metadata.py

## Phase 9: User Story 7 - 실행 위치 무관 데이터, 단일 실행, Windows CLI (P2)

**Goal**: 앱 루트 chdir, 로깅 방어, 단일 인스턴스, CLI 루프 정책 제거, 간격 식별자/UTC 비교
**Independent Test**: tests/test_app_paths.py, tests/test_single_instance.py, tests/test_event_loop_policy.py, tests/test_keyword_interval.py

- [x] T031 [P] [US7] 앱 루트·로깅 방어 테스트 in tests/test_app_paths.py
- [x] T032 [P] [US7] 단일 인스턴스 잠금 테스트 in tests/test_single_instance.py
- [x] T033 [P] [US7] 이벤트 루프 정책 미사용 테스트 in tests/test_event_loop_policy.py
- [x] T034 [P] [US7] 간격 UTC 비교·서명 분리 테스트 in tests/test_keyword_interval.py
- [x] T035 [US7] `app_root()`, `ensure_app_root_cwd()` 구현 in app_paths.py
- [x] T036 [US7] main에서 앱 루트 chdir, setup_logging 방어, CLI 정책 제거 in main.py
- [x] T037 [US7] QLockFile 단일 인스턴스 가드 in gui/app.py (+ gui/single_instance.py)
- [x] T038 [US7] 간격 판정을 서명 기반 메모리 + UTC 비교 DB 조회로 변경 in engine/search_flow.py, storage/stats_sections/record.py
- [x] T039 [US7] PyInstaller 번들에 신규 모듈 포함 확인 in used_market_notifier.spec, pyproject.toml

## Phase 10: User Story 8 - 비밀값·설정·내보내기 안전 (P3)

**Goal**: DPAPI 비밀값, 원자적 설정 저장, 내보내기 정제
**Independent Test**: tests/test_settings_secrets.py, tests/test_export_sanitize.py

- [x] T040 [P] [US8] DPAPI 왕복/평문 호환/복호화 실패/원자적 저장 테스트 in tests/test_settings_secrets.py
- [x] T041 [P] [US8] 내보내기 정제 테스트 in tests/test_export_sanitize.py
- [x] T042 [US8] DPAPI protect/unprotect 구현 in app_settings/secrets.py
- [x] T043 [US8] 직렬화/역직렬화에 비밀값 보호 적용 in app_settings/mixins/serialization.py, app_settings/mixins/deserialization.py
- [x] T044 [US8] 원자적 save(임시 파일 + os.replace) in app_settings/manager.py 및 recovery 쓰기 경로 in app_settings/mixins/recovery.py
- [x] T045 [US8] 복호화 실패 시작 안내 in gui/main/window_mixins/recovery.py
- [x] T046 [US8] 셀 정제 구현 in export_manager.py

## Phase 11: User Story 9 - last_seen 기반 정리 (P3)

**Goal**: 최근 확인 매물은 정리에서 보존
**Independent Test**: tests/test_cleanup_last_seen.py

- [x] T047 [P] [US9] 정리 보존/삭제 테스트 in tests/test_cleanup_last_seen.py
- [x] T048 [US9] 플랫폼 처리 후 listing last_seen 기록 in engine/search_flow.py
- [x] T049 [US9] 정리·미리보기 기준을 COALESCE(last_seen, created_at)로 변경 in storage/maintenance.py

## Phase 12: Polish & Cross-Cutting Concerns

- [x] T050 [P] README 테스트 수·복원·알림 정책·경로·단일 실행 설명 정정 in README.md
- [x] T051 [P] CLAUDE.md 비동기 패턴·퍼지 중복·PySide6 예제·2026-09 remediation 섹션 갱신, 파일명 대소문자 정정(claude.md → CLAUDE.md)
- [x] T052 [P] AGENTS.md 추가(CLAUDE.md 참조) in AGENTS.md
- [x] T053 [P] PROJECT_AUDIT.md에 조치 상태 반영 in PROJECT_AUDIT.md
- [x] T054 전체 테스트·오프스크린 GUI 스모크·pyright(가능 시) 실행 및 UTF-8 위생 확인

## Dependencies & Execution Order

- Phase 2(T002~T005)는 US2, US4, US9의 선행 조건이다.
- US1(T006~T007)은 독립이다. US3(T012~T016)은 대기형 stop 계약에 의존하므로 T025와 함께 검증한다.
- US5의 T023은 US2의 T010과 같은 파일(search_flow.py)이므로 T010 이후에 수행한다. T029·T038·T048도 search_flow.py라 순차 수행한다.
- US6의 T028은 T030보다 먼저 수행한다.
- Polish는 모든 스토리 이후에 수행한다.

### Parallel Opportunities

- 각 스토리의 테스트 작성 태스크 [P]는 서로 다른 파일이라 병렬 가능하다.
- T002/T003, T031~T034, T040/T041, T050~T053은 병렬 가능하다.

## Implementation Strategy

1. **MVP**: Phase 2 + US1(복원 손상 제거) → US3(host) → US2(기준선) 순으로 데이터 손상과 알림 폭주를 먼저 제거한다.
2. 이후 US4 → US5 → US6 → US7 → US8 → US9를 순서대로 진행하고, 각 스토리 완료 시 전체 테스트를 실행한다.
3. 마지막으로 문서를 정정하고 최종 검증한다.
