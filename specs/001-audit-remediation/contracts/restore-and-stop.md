# Contract: Restore & monitor stop

## `BackupManager.restore_backup(backup_file, db_path, settings_path) -> bool`

- 반환 True: 백업 DB가 무결성 검사를 통과했고, `db_path`의 내용이 백업 시점과 같아졌으며, 설정도 복원되었다.
- 반환 False: 현재 `db_path`와 설정은 변경되지 않았다(부분 적용 없음).
- 부수 효과: 복원 전에 `"{db_path}.pre_restore"`(현재 DB의 일관된 전체 사본, WAL 포함)와 `"{settings_path}.pre_restore"`를 만든다.
- 다른 연결이 `db_path`를 열고 있어도 안전하다. 그 연결은 복원 후 새 내용을 본다.
- ZIP 경로 검증(allowlist/Zip Slip 방어)은 기존과 동일하다.

## `MonitorThread`

| 메서드 | 블로킹 | 의미 |
|--------|--------|------|
| `request_stop()` | 아니오 | 엔진에 중지 신호를 보낸다. 여러 번 호출해도 안전하다. |
| `stop(timeout_ms=30000) -> bool` | 예 | `request_stop()` 후 스레드 종료까지 대기한다. 제한 시간 내 종료되면 True. 레거시 호출 호환용이다. |

## MainWindow 모니터링 상태 전이

```
idle --start--> running --stop--> stopping --finished--> idle
                   ^                  |
                   |   start 요청     v
                   +---- pending_start(finished 후 자동 시작)
```

- `stopping` 동안의 시작 요청은 `pending_start`로 보류한다.
- 동시에 존재하는 엔진 스레드는 항상 1개 이하다.
- 프로세스 첫 엔진만 `suppress_initial_notifications=True`로 만든다.
