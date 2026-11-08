from apps.backend.api.security.security import hash_password, verify_password


def test_hash_password_produces_salt_dollar_digest_format():
    hashed = hash_password("correct horse battery staple")
    salt_hex, digest_hex = hashed.split("$")
    assert len(salt_hex) == 32  # 16-byte salt, hex-encoded
    assert len(digest_hex) == 64  # sha256 digest, hex-encoded


def test_hash_password_is_salted_and_not_deterministic():
    first = hash_password("same-password")
    second = hash_password("same-password")
    assert first != second


def test_verify_password_accepts_the_correct_password():
    hashed = hash_password("s3cr3t!")
    assert verify_password("s3cr3t!", hashed) is True


def test_verify_password_rejects_an_incorrect_password():
    hashed = hash_password("s3cr3t!")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_rejects_a_malformed_stored_hash():
    assert verify_password("anything", "not-a-valid-hash") is False
