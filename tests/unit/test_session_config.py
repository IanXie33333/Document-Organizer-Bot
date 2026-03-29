from db.session import SessionLocal


def test_session_does_not_expire_on_commit() -> None:
    assert SessionLocal.kw.get('expire_on_commit') is False
