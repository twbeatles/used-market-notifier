# Data Model: Audit Remediation 2026-09

기존 테이블 구조는 변경하지 않는다. 아래 두 테이블을 `CREATE TABLE IF NOT EXISTS`로 추가한다.

## search_baselines (신규)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| signature | TEXT NOT NULL | 정규화된 키워드 검색 조건 서명 |
| platform | TEXT NOT NULL | `danggeun` / `bunjang` / `joonggonara` |
| established_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | 첫 성공 검색 시각(UTC) |

- PK: `(signature, platform)`
- 쓰기 규칙: 한 플랫폼 검색이 오류 없이 완료(결과 0건 포함, 백오프/미가용/중지는 제외)되면 `INSERT OR IGNORE`한다.
- 서명 규칙: `"|".join([norm(keyword), norm(location), str(min_price or 0), str(max_price or 0), ",".join(sorted(norm(x) for x in exclude_keywords))])`. `norm`은 strip + 연속 공백 1칸 + 소문자다.
- 마이그레이션: 기존 DB에는 기준선이 없다. 업그레이드 직후 첫 모니터링은 프로세스 첫 엔진이라 억제되므로 폭주가 없고, 그 사이클에서 기준선이 채워진다.

## listing_last_seen (신규)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| listing_id | INTEGER PRIMARY KEY REFERENCES listings(id) | 매물 id |
| last_seen_at | TIMESTAMP NOT NULL | 마지막으로 검색 결과에서 본 시각(UTC) |

- 쓰기 규칙: 플랫폼별 처리 후 이번에 저장/갱신된 listing id들을 한 번의 `executemany` + commit으로 upsert한다.
- 정리 규칙: 삭제 대상 = `COALESCE(last_seen_at, created_at) < datetime('now', '-N days')`. 삭제 순서에 `listing_last_seen`을 추가한다(listings보다 먼저).

## meta

- `price_parse_version`: 2 → **3**(ISSUE-007 부분 처리 DB 재계산)

## 가격 규칙 (listings 갱신)

| 기존 가격 | 수신 가격 | 결과 |
|-----------|-----------|------|
| known A | known B, 숫자 다름 | 가격 변동 기록 + 알림(기존 동작) |
| known A | unknown(`가격문의`, 빈 값 등) | 가격 유지, 변동 없음 |
| unknown | known B | 가격 채움, 변동 기록/알림 없음 |
| unknown | unknown | 변동 없음 |
| known `1만원` | known `무료나눔`(0) | 가격 변동(0은 known) |

## 판매 상태 규칙

| 명시 상태 | 제목 단서 | 기존 매물 결과 | 신규 매물 결과 |
|-----------|-----------|----------------|----------------|
| 있음 | - | 명시 상태 | 명시 상태 |
| 없음 | 있음 | 제목 단서 | 제목 단서 |
| 없음 | 없음 | **기존 상태 유지** | `for_sale` |

## Item (모델)

- `notification_suppressed: bool = False`(`compare=False`, `repr=False`)를 추가한다. 엔진이 알림 억제 시 True로 설정하고, GUI는 트레이 알림 여부를 이 값으로 판단한다.

## 설정 JSON (역호환)

- `notifiers[].token`, `notifiers[].webhook_url`: Windows 저장 시 `dpapi:v1:<base64>`. 로드 시 접두어가 없으면 평문으로 사용한다(구버전 호환). 복호화 실패 시 `""`로 바꾸고 `load_recovery_state["secret_decrypt_failed"] = [필드 목록]`에 기록한다.
