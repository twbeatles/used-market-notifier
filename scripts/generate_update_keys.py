"""Ed25519 업데이트 서명 키를 만들고 GitHub secret에 저장합니다.

공개키는 이 스크립트가 소스의 UPDATE_PUBLIC_KEY_B64_DEFAULT 를 바꾸지 않습니다.
새 키를 쓰면 constants.py의 공개키를 바꾼 실행 파일을 먼저 배포해야 합니다.
개인키는 출력하지 않습니다.
"""

from __future__ import annotations

import base64
import subprocess

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generate_keypair() -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return (
        base64.b64encode(private_bytes).decode("ascii"),
        base64.b64encode(public_bytes).decode("ascii"),
    )


def set_github_secret(name: str, value: str) -> None:
    proc = subprocess.run(
        ["gh", "secret", "set", name, "--body", value],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to set GitHub secret {name}: {proc.stderr.strip()}")
    print(f"[OK] GitHub secret set: {name}")


def main() -> int:
    private_b64, public_b64 = generate_keypair()
    print(f"PUBLIC_KEY_B64: {public_b64}")
    print("Put this public key in updater/constants.py UPDATE_PUBLIC_KEY_B64_DEFAULT,")
    print("then ship a build that embeds it before publishing manifests signed by the new key.")
    set_github_secret("UMN_UPDATE_PUBLIC_KEY_B64", public_b64)
    set_github_secret("UMN_UPDATE_PRIVATE_KEY_B64", private_b64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
