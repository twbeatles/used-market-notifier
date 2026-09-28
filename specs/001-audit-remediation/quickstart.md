# Quickstart: Audit Remediation 검증

## 준비

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

기대: 전체 통과, 신규 회귀 테스트 포함.

## 시나리오별 회귀 테스트

| 요구사항 | 테스트 모듈 | 기대 |
|----------|-------------|------|
| FR-001~002 복원 | `tests/test_restore_live_db.py` | 열린 WAL 연결 + 300행 추가 후 복원 → integrity ok, 행 수 = 백업 시점. pre_restore 행 수 = 복원 직전 |
| FR-003~004 host | `tests/test_settings_host.py` | 오프스크린 MainWindow에서 host 해석 = MainWindow, 차단 목록 1→해제 0, 복원 전 stop 호출 |
| FR-005 마이그레이션 | `tests/test_price_migration_batches.py` | 1200행 전부 재계산 |
| FR-006~009 기준선/상한 | `tests/test_notification_baseline.py` | 키워드 추가 후 알림 0, 재시작 후 신규 1건 알림, 상한 15 + 요약 1 |
| FR-010~012 가격/상태 | `tests/test_listing_price_status_rules.py` | 왕복 변동 0, 무료나눔은 변동, sold 유지 |
| FR-013~015 중지 | `tests/test_monitor_stop.py` | 중지 후 추가 검색 0, `request_stop` 비블로킹, 재시작 직렬화 |
| FR-016~017 폴백 | `tests/test_fallback_lifecycle.py` | 보강 10건 재생성 0, 지연 생성, 쿨다운 |
| FR-018 루프 | `tests/test_event_loop_policy.py` | 코드에 `set_event_loop_policy` 없음, CLI가 Selector 정책 미설정 |
| FR-019 간격 | `tests/test_keyword_interval.py` | UTC 비교 정확, 서명별 분리 |
| FR-020~021 경로/로깅 | `tests/test_app_paths.py` | app_root 해석, 쓰기 불가 로그 경로에서도 setup_logging 무예외 |
| FR-022 단일 인스턴스 | `tests/test_single_instance.py` | 두 번째 잠금 획득 실패 |
| FR-023~024 설정 | `tests/test_settings_secrets.py` | 원자적 저장, DPAPI 왕복(Windows), 평문 호환, 복호화 실패 처리 |
| FR-025 내보내기 | `tests/test_export_sanitize.py` | `=1+1` → 문자열 셀 |
| FR-026 정리 | `tests/test_cleanup_last_seen.py` | 최근 확인 매물 보존 |

## 수동 확인 (선택)

1. `python main.py`를 실행한 뒤 다른 터미널에서 다시 실행 → "이미 실행 중" 안내 후 종료.
2. 모니터링 중 중지 버튼 → 즉시 "중지 중" 표시, 창 멈춤 없음.
3. 설정 > 차단 관리에서 목록 표시와 해제 동작 확인.
4. `C:\` 같은 다른 폴더에서 `python <repo>\main.py --cli` 실행 → 저장소 폴더의 `settings.json` 사용.
