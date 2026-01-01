import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    Paper,
    PaperAuthor,
    PaperPublic,
    PapersPublic,
    PaperSubmission,
    PaperVersion,
    Person,
)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/", response_model=PaperPublic)
def submit_paper(
    *, session: SessionDep, current_user: CurrentUser, submission: PaperSubmission
) -> Any:
    """Submit a new paper with its first version and authors."""
    if not current_user.person_id:
        raise HTTPException(
            status_code=400,
            detail="User must have a linked Person profile to submit papers",
        )

    author_person_ids = [a.person_id for a in submission.authors]
    if current_user.person_id not in author_person_ids:
        raise HTTPException(
            status_code=400,
            detail="Submitter must be listed as an author",
        )

    existing_persons = session.exec(
        select(Person).where(Person.id.in_(author_person_ids))
    ).all()
    existing_ids = {p.id for p in existing_persons}
    missing_ids = set(author_person_ids) - existing_ids
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Person(s) not found: {[str(pid) for pid in missing_ids]}",
        )

    paper = Paper(title=submission.title, abstract=submission.abstract)
    session.add(paper)
    session.flush()

    version = PaperVersion(
        paper_id=paper.id,
        version_number=1,
        pdf_url=submission.pdf_url,
    )
    session.add(version)

    for position, author_input in enumerate(submission.authors, start=1):
        paper_author = PaperAuthor(
            paper_id=paper.id,
            person_id=author_input.person_id,
            author_position=position,
            is_corresponding=author_input.is_corresponding,
        )
        session.add(paper_author)

    session.commit()
    session.refresh(paper)
    return paper


@router.get("/", response_model=PapersPublic)
def list_papers(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """List papers. Authors see their papers, superusers see all."""
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Paper)
        count = session.exec(count_statement).one()
        statement = (
            select(Paper)
            .order_by(Paper.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        papers = session.exec(statement).all()
    else:
        if not current_user.person_id:
            return PapersPublic(data=[], count=0)

        count_statement = (
            select(func.count())
            .select_from(Paper)
            .join(PaperAuthor)
            .where(PaperAuthor.person_id == current_user.person_id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Paper)
            .join(PaperAuthor)
            .where(PaperAuthor.person_id == current_user.person_id)
            .order_by(Paper.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        papers = session.exec(statement).all()

    return PapersPublic(data=papers, count=count)


@router.get("/{paper_id}", response_model=PaperPublic)
def get_paper(
    session: SessionDep, current_user: CurrentUser, paper_id: uuid.UUID
) -> Any:
    """Get paper by ID."""
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not current_user.is_superuser:
        if not current_user.person_id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        is_author = session.exec(
            select(PaperAuthor).where(
                PaperAuthor.paper_id == paper_id,
                PaperAuthor.person_id == current_user.person_id,
            )
        ).first()
        if not is_author:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    return paper
