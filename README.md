# 🥕 중고거래 알리미 (Used Market Notifier)

당근마켓, 번개장터, 중고나라에서 원하는 물건을 실시간으로 검색하고 알림을 받아보세요.
현대적인 UI와 강력한 필터링 기능으로 중고거래를 더욱 스마트하게 도와줍니다.

## ✨ 주요 기능

*   **다중 플랫폼 지원**: 당근마켓, 번개장터, 중고나라 동시 모니터링
*   **현대적인 GUI**: Tokyo Night 테마가 적용된 세련된 다크 모드 인터페이스
*   **실시간 알림**:
    *   **텔레그램**: 봇을 통한 메시지 및 썸네일 알림
    *   **디스코드**: 웹훅을 통한 엠베드 알림
    *   **슬랙**: 웹훅을 통한 메시지 알림
    *   **알림 테스트**: 설창 창에서 즉시 발송 테스트 가능
*   **강력한 필터링**:
    *   최소/최대 가격 설정
    *   제외 키워드 설정 (예: "케이스", "부품")
    *   지역 필터링 (당근마켓 한정)
*   **통계 대시보드**:
    *   검색 통계, 플랫폼별 분포, 가격 변동 추이 시각화
    *   **링크 열기**: 테이블 항목 더블 클릭 시 상품 페이지 이동
*   **백그라운드 실행**: 시스템 트레이 최소화 모드 지원
*   **방해 금지 모드**: 특정 요일/시간대에만 알림 받도록 스케줄 설정

## �️ 설치 방법

### 요구 사항
*   Windows 10/11
*   Python 3.10 이상
*   Chrome 브라우저 (Google Chrome)

### 1. 소스 코드 다운로드
```bash
git clone https://github.com/yourusername/used-market-notifier.git
cd used-market-notifier
```

### 2. 가상 환경 생성 (권장)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

## 🚀 실행 방법

### 소스 코드로 실행
```bash
python main.py
```

### 실행 파일 빌드 (선택 사항)
PyInstaller를 사용하여 단일 실행 파일(.exe)로 만들 수 있습니다.

```bash
pip install pyinstaller
pyinstaller used_market_notifier.spec
```
빌드가 완료되면 `dist` 폴더에 `UsedMarketNotifier.exe`가 생성됩니다.

## ⚙️ 설정 가이드

### 1. 키워드 추가
- **키워드 탭**에서 `+ 새 키워드` 버튼 클릭
- 검색어, 가격 범위, 제외 키워드 입력
- 모니터링할 플랫폼 선택

### 2. 알림 설정 (텔레그램 예시)
1. 텔레그램에서 `@BotFather` 검색 후 `/newbot`으로 봇 생성 -> **Token** 획득
2. `@userinfobot` 검색 후 본인의 **Chat ID** 확인
3. 프로그램 설정 -> 텔레그램 탭에 Token과 Chat ID 입력 및 활성화
4. **중요**: 생성한 봇에게 텔레그램에서 먼저 아무 메시지나("/start") 보내야 알림이 옵니다.
5. 설정 창 하단의 **"테스트 알림 보내기"** 버튼으로 정상 작동을 확인하세요.

## 📝 라이선스
MIT License
