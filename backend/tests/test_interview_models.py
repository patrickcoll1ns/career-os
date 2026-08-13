from app.models.interview import InterviewSession, InterviewTurn


def test_interview_session_table_has_expected_columns() -> None:
    assert set(InterviewSession.__table__.columns.keys()) == {
        "id",
        "owner_id",
        "target_role",
        "interview_type",
        "difficulty",
        "question_limit",
        "status",
        "summary",
        "strengths",
        "improvements",
        "learning_recommendations",
        "error_message",
        "created_at",
        "updated_at",
    }


def test_interview_session_configuration_is_constrained() -> None:
    constraint_names = {
        constraint.name for constraint in InterviewSession.__table__.constraints
    }

    assert {
        "ck_interview_sessions_type",
        "ck_interview_sessions_difficulty",
        "ck_interview_sessions_status",
        "ck_interview_sessions_question_limit",
    } <= constraint_names


def test_interview_turn_table_has_expected_columns() -> None:
    assert set(InterviewTurn.__table__.columns.keys()) == {
        "id",
        "session_id",
        "sequence_number",
        "question",
        "answer",
        "feedback",
        "created_at",
        "updated_at",
    }


def test_interview_turn_order_is_unique_within_session() -> None:
    constraint_names = {
        constraint.name for constraint in InterviewTurn.__table__.constraints
    }

    assert "uq_interview_turns_session_sequence" in constraint_names
    assert "ck_interview_turns_sequence_number" in constraint_names


def test_interview_turns_are_deleted_with_their_session() -> None:
    foreign_key = next(iter(InterviewTurn.__table__.c.session_id.foreign_keys))

    assert foreign_key.target_fullname == "interview_sessions.id"
    assert foreign_key.ondelete == "CASCADE"
