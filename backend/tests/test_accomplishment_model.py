from app.models.accomplishment import Accomplishment


def test_accomplishment_table_has_expected_columns() -> None:
    assert set(Accomplishment.__table__.columns.keys()) == {
        "id",
        "title",
        "description",
        "achieved_on",
        "created_at",
        "updated_at",
    }
