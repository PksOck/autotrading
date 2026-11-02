from preza.services.owner_access import hash_password, verify_password


def test_owner_password_is_salted_and_never_stored_in_plaintext():
    password = "a long synthetic test password"
    first, second = hash_password(password), hash_password(password)
    assert first != second and password not in first
    assert verify_password(password, first)
    assert not verify_password("wrong", first)
    assert not verify_password(password, "bad hash")
