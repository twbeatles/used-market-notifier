# Research: Audit Remediation 2026-09

## R1. WAL DB에 안전하게 복원하는 방법

- **Decision**: 추출한 백업 DB를 소스로, `db_path`에 새로 연 연결을 대상으로 `sqlite3.Connection.backup()`(online backup API)을 사용한다. 복원 전 소스 `PRAGMA integrity_check == ok`를 검증한다. `.pre_restore`는 현재 DB를 소스로 backup API를 써서 새 파일로 만든다(기존 파일은 먼저 삭제).
- **Rationale**: backup API는 대상 DB의 pager/WAL을 통해 쓰므로, 다른 열린 연결(MainWindow.db)이 있어도 WAL 프레임과 일관된다. 감사에서 재현한 "파일 덮어쓰기 + 잔존 WAL 재생" 문제가 원천적으로 사라진다. 실패하면 트랜잭션이 적용되지 않아 현재 DB는 그대로다.
- **Alternatives considered**:
  - 모든 연결을 닫고 `-wal`/`-shm` 삭제 후 복사: 위젯 standalone 연결까지 추적해야 하고, 누락 시 여전히 손상된다.
  - 다음 시작 시 적용하는 보류 복원: 안전하지만 UX가 복잡하고 즉시 검증이 불가능하다.
- **주의**: WAL 대상은 페이지 크기가 다르면 backup이 실패한다. 이 앱은 기본 4096을 쓰므로 실사용에서 문제가 없고, 실패 시 오류로 보고한다.

## R2. 알림 기준선 단위와 저장

- **Decision**: 새 테이블 `search_baselines(signature TEXT, platform TEXT, established_at, PRIMARY KEY(signature, platform))`. 서명은 정규화한 `keyword|location|min|max|exclude(sorted)`다.
- **Rationale**: 키워드 추가/텍스트 변경/필터 변경 모두 새 서명이 되어 첫 검색이 기준선이 된다. 엔진 재시작과 무관하게 영속된다. 토글(비활성→활성)은 서명이 같아 기준선이 유지되며, 비활성 기간 신규 매물은 실제 신규로 알린다(상한 적용).
- **Alternatives**: `search_stats` 존재 여부 — 실패 검색도 기록되어 부적합하다. 메모리 dict — 재시작 시 소실된다.

## R3. 첫 실행 억제 범위

- **Decision**: 프로세스 수명 동안 첫 번째 엔진만 첫 사이클을 억제한다(`suppress_initial_notifications`). 이후 재시작은 억제하지 않는다.
- **Rationale**: README의 "프로그램 시작 시 폭풍 방지" 정책은 유지하면서 설정 저장 재시작 시의 누락(ISSUE-002c)을 제거한다. 새 키워드 폭주는 기준선이 막는다.

## R4. 비차단 모니터링 중지

- **Decision**: `MonitorThread.request_stop()` → `loop.call_soon_threadsafe(engine._request_stop)`(running=False, stop_event.set). 엔진 `run_cycle`은 키워드마다, `search_keyword`는 플랫폼 처리마다 `self.running`을 확인한다. 창은 `QThread.finished`에서 UI 상태 복원·참조 해제·대기 중 재시작을 수행한다. 대기형 `stop(timeout)`은 종료/복원/업데이트에서만 쓴다.
- **Rationale**: UI 스레드 블로킹 제거, QThread 참조 유지로 비정상 종료 방지, 이전 스레드 종료 후에만 재시작.
- **Alternatives**: timeout 조정만 하는 방식은 블로킹이 남는다.

## R5. 폴백 스크래퍼 수명

- **Decision**: 지연 생성 + 600초 실패 쿨다운. 폴백 unhealthy이면 폴백만 교체한다. 보강 루프는 `_has_fallback_option(platform)`이 False면 건너뛴다.
- **Rationale**: ISSUE-005 해결과 상주 브라우저 절반 감소를 함께 얻는다. 검색 경로의 기존 계약(`fallback_scrapers` dict 직접 주입 테스트)도 유지된다.

## R6. 가격 placeholder 판별

- **Decision**: `price_utils.is_unknown_price_text(text)`: 공백 제거·소문자화 후 빈 문자열, 또는 `가격문의`/`문의`/`가격협의`/`협의`/`가격미정`/`미정`/`n/a`/`na`/`-`/`가격없음`/`정보없음`이거나, 숫자가 없고 무료 키워드도 없는 텍스트이면 unknown으로 본다. `무료`/`나눔`/`0원`은 known 0이다.
- **Rationale**: 파서 수정 없이 저장 계층에서 왕복을 차단한다.

## R7. 판매 상태 유지

- **Decision**: `detect_sale_status`에 `default` 인자를 추가한다(기존 호출 호환을 위해 기본 `"for_sale"`). `add_listing`의 기존 매물 경로는 `default=None`으로 호출해 단서가 없으면 기존 상태를 유지한다.

## R8. 앱 데이터 경로

- **Decision**: `app_paths.app_root()` = frozen이면 `Path(sys.executable).parent`, 아니면 `main.py`가 있는 폴더. `main()` 시작 시 `os.chdir(app_root())`.
- **Rationale**: 상대 경로 사용처 20여 곳을 한 번에 일관화하고, 업데이터의 `app_storage_root()`와 기준이 같아진다. 테스트는 `main()`을 호출하지 않으므로 영향이 없다.
- **로깅 방어**: 파일 핸들러 생성을 try/except로 감싼다. `sys.stdout`이 None이면 콘솔 핸들러를 생략한다.

## R9. 단일 인스턴스

- **Decision**: `QLockFile(<app_root>/.used_market_notifier.lock)`, `setStaleLockTime(0)` + `tryLock(100)`. 실패 시 안내 메시지 후 종료 코드 0으로 끝낸다. 스모크 모드(`_run_gui_smoke_if_requested`)는 그 전에 반환하므로 제외된다. 환경변수 `USED_NOTIFIER_ALLOW_MULTI=1`로 우회할 수 있다(개발용).
- **Rationale**: QLockFile은 PID 기반 stale lock 감지를 지원한다.

## R10. DPAPI

- **Decision**: ctypes로 `crypt32.CryptProtectData`/`CryptUnprotectData`, `CRYPTPROTECT_UI_FORBIDDEN`, 고정 entropy `b"UsedMarketNotifier.v1"`. 저장 형식은 `dpapi:v1:<base64>`.
- **Rationale**: 추가 의존성 없이 사용자 계정 바인딩 암호화를 제공한다. 비Windows 또는 API 실패 시 평문을 유지해(보호 실패가 저장 실패로 이어지지 않도록) 경고 로그를 남긴다.

## R11. 내보내기 정제

- **Decision**: 문자열 값이 `= + - @ \t \r`로 시작하면 `'`를 붙인다(OWASP). xlsx는 문자열 셀의 `data_type`을 `"s"`로 강제한다. 숫자 타입 값은 그대로 둔다.

## R12. 간격 식별자 + UTC 비교 버그

- **Decision**: 엔진 메모리에 `_keyword_last_run[signature]`(monotonic)를 둔다. 미기록 시 DB `get_last_search_time(keyword, platforms)`를 UTC 기준으로 비교한다(`search_stats.checked_at`은 SQLite `CURRENT_TIMESTAMP` = UTC).
- **근거**: 감사 후 추가 발견. 기존 코드는 UTC 시각을 로컬 `datetime.now()`와 비교해 KST에서 +9시간 오차가 났고, 540분 미만 간격은 항상 경과로 판정되었다.

## R13. deprecated asyncio 정책 API

- **Decision**: GUI 스레드는 win32에서 `asyncio.ProactorEventLoop()`를 직접 생성하고, 그 외는 `new_event_loop()`를 쓴다. CLI는 정책을 설정하지 않는다(Windows 기본 Proactor). `set_event_loop_policy` 사용을 제거한다.
