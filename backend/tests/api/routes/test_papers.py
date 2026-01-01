import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import Person, PersonRole, User


def test_submit_paper(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Get superuser's person_id
    user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
    assert user is not None
    assert user.person_id is not None

    data = {
        "title": "Test Paper Title",
        "abstract": "This is a test abstract.",
        "pdf_url": "https://arxiv.org/pdf/1234.5678",
        "authors": [{"person_id": str(user.person_id), "is_corresponding": True}],
    }
    response = client.post(
        f"{settings.API_V1_STR}/papers/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["abstract"] == data["abstract"]
    assert "id" in content
    assert "created_at" in content


def test_submit_paper_without_person_fails(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # Normal user doesn't have a person_id by default
    data = {
        "title": "Test Paper",
        "abstract": "Abstract",
        "pdf_url": "https://example.com/paper.pdf",
        "authors": [{"person_id": str(uuid.uuid4()), "is_corresponding": True}],
    }
    response = client.post(
        f"{settings.API_V1_STR}/papers/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "person profile" in content["detail"].lower()


def test_list_papers(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/papers/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert isinstance(content["data"], list)


def test_get_paper_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/papers/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Paper not found"


def test_submit_paper_requires_submitter_as_author(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Create a different person who is not the submitter
    other_person = Person(
        display_name="Other Person",
        email="other@example.com",
        role=PersonRole.researcher,
    )
    db.add(other_person)
    db.commit()
    db.refresh(other_person)

    data = {
        "title": "Test Paper",
        "abstract": "Abstract",
        "pdf_url": "https://example.com/paper.pdf",
        "authors": [{"person_id": str(other_person.id), "is_corresponding": True}],
    }
    response = client.post(
        f"{settings.API_V1_STR}/papers/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "submitter must be listed as an author" in content["detail"].lower()
