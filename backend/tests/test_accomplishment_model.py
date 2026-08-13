from app.models.accomplishment import Accomplishment


def test_accomplishment_table_has_expected_columns() -> None:
    assert set(Accomplishment.__table__.columns.keys()) == {
        "id",
        "owner_id",
        "title",
        "description",
        "achieved_on",
        "archived_at",
        "created_at",
        "updated_at",
    }
