from app.models.resume_review import ResumeReview


def test_resume_review_table_has_expected_columns() -> None:
    assert set(ResumeReview.__table__.columns.keys()) == {
        "id",
        "owner_id",
        "document_id",
        "target_role",
        "status",
        "summary",
        "strengths",
        "gaps",
        "rewrite_suggestions",
        "error_message",
        "created_at",
        "updated_at",
    }


def test_resume_review_status_is_constrained() -> None:
    constraint_names = {
        constraint.name for constraint in ResumeReview.__table__.constraints
    }

    assert "ck_resume_reviews_status" in constraint_names


def test_resume_review_is_deleted_with_its_source_document() -> None:
    foreign_key = next(iter(ResumeReview.__table__.c.document_id.foreign_keys))

    assert foreign_key.target_fullname == "documents.id"
    assert foreign_key.ondelete == "CASCADE"
