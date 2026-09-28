# Contract: Settings panel host

Settings mixin(`gui/settings_panels/mixins/*`)은 `self.parent()`에 의존하지 않고 `gui/settings_panels/host.py:resolve_settings_host(widget)`로 host를 얻는다.

## 해석 순서

1. `widget.window()`가 아래 계약 속성 중 `stop_monitoring`을 가지면 그것을 host로 쓴다.
2. 아니면 `widget.parent()`(레거시 `SettingsDialog`의 부모가 MainWindow인 경우)를 host로 쓴다.
3. 둘 다 아니면 `None`.

## Host 계약 (MainWindow가 제공)

| 멤버 | 타입 | 의미 |
|------|------|------|
| `db` | `DatabaseManager` | UI 수명 공유 DB 연결 |
| `engine` | `MonitorEngine \| None` | 현재 엔진 |
| `is_monitoring_active()` | `() -> bool` | 실행 중이거나 중지 중인 모니터 스레드가 있음 |
| `stop_monitoring(wait: bool = False, timeout_ms: int = 30000)` | `-> bool` | `wait=True`이면 종료까지 대기하고 성공 여부 반환 |
| `stats_widget.refresh_stats()`, `listings_widget.refresh_listings()` | 선택 | 정리 후 새로고침 |

## 동작 규칙

- **복원**: host가 없거나 `stop_monitoring(wait=True)`가 False이면 복원을 거부하고 경고를 표시한다.
- **지금 정리**: 모니터링이 활성이면 확인을 받고 `stop_monitoring(wait=True)` 성공 시에만 진행한다.
- **차단 판매자 조회/해제**: `host.db`(없으면 `host.engine.db`)를 사용한다. 둘 다 없으면 오류 메시지를 표시한다.
