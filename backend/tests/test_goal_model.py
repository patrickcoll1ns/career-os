from app.models.goal import Goal


def test_goal_table_has_expected_columns() -> None:
    assert set(Goal.__table__.columns.keys()) == {
        "id",
        "title",
        "description",
        "status",
        "target_date",
        "archived_at",
        "created_at",
        "updated_at",
    }


def test_goal_status_is_constrained() -> None:
    constraint_names = {constraint.name for constraint in Goal.__table__.constraints}

    assert "ck_goals_status" in constraint_names
