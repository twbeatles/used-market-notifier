# Used Market Notifier Update Manifests

이 디렉터리의 `latest.json`은 GitHub Actions 릴리즈 워크플로가 `main`에 갱신하는 서명된 업데이트 매니페스트입니다.

포함 항목:

- 버전
- HTTPS 다운로드 URL
- SHA-256
- 파일 크기
- 만료 시각
- Ed25519 서명

앱은 `updater/constants.py`에 들어 있는 공개키로 서명을 확인한 뒤에만 파일을 받습니다. 개인키는 GitHub secret `UMN_UPDATE_PRIVATE_KEY_B64`에만 둡니다.

릴리즈는 `version.py`의 `__version__`과 같은 `vX.Y.Z` 태그를 `main`에 푸시하면 만들어집니다.

저장소에 들어 있는 `latest.json`은 현재 앱 버전과 같은 서명된 포인터입니다. 버전이 같으면 앱은 파일을 받지 않습니다. 첫 태그 릴리즈가 실제 exe의 URL, 크기, SHA-256으로 이 파일을 바꿉니다.
