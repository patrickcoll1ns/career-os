from app.models.document import Document


def test_document_table_has_expected_columns() -> None:
    assert set(Document.__table__.columns.keys()) == {
        "id",
        "owner_id",
        "original_filename",
        "content_type",
        "size_bytes",
        "sha256",
        "storage_key",
        "status",
        "extracted_text",
        "error_message",
        "created_at",
        "updated_at",
    }


def test_document_status_and_size_are_constrained() -> None:
    constraint_names = {
        constraint.name for constraint in Document.__table__.constraints
    }

    assert "ck_documents_status" in constraint_names
    assert "ck_documents_size_bytes" in constraint_names


def test_document_storage_key_is_unique() -> None:
    storage_key = Document.__table__.columns["storage_key"]

    assert storage_key.unique is True
