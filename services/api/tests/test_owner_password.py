import bcrypt
import pytest

from preza.services.owner_access import hash_password, valid_hash, verify_password


def test_owner_password_is_salted_and_never_stored_in_plaintext():
    password = "a long synthetic test password"
    first, second = hash_password(password), hash_password(password)
    assert first != second and password not in first
    assert verify_password(password, first)
    assert not verify_password("wrong", first)
    assert not verify_password(password, "bad hash")


@pytest.mark.parametrize("prefix", [b"2a", b"2b", b"2y"])
def test_existing_bcrypt_owner_hash_is_supported(prefix):
    password = "synthetic bcrypt owner password"
    encoded = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    encoded = "$" + prefix.decode() + encoded[3:]
    assert valid_hash(encoded)
    assert verify_password(password, encoded)
    assert not verify_password("wrong password", encoded)
    assert not verify_password(password + "x" * 72, encoded)


def test_bcrypt_does_not_truncate_utf8_passwords_or_accept_unbounded_costs():
    password = "é" * 36
    encoded = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    assert verify_password(password, encoded)
    assert not verify_password(password + "é", encoded)
    for value in [encoded[:4] + "31" + encoded[6:], encoded[:-1], encoded + "x"]:
        assert not valid_hash(value)
        assert not verify_password(password, value)


def test_malformed_bcrypt_salt_fails_closed():
    assert not verify_password("synthetic test password", "$2b$12$" + "A" * 53)
