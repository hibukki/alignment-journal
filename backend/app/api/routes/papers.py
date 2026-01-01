import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentEditor, CurrentUser, SessionDep
from app.models import (
    Decision,
    DecisionCreate,
    DecisionPublic,
    DeskDecision,
    DeskDecisionCreate,
    DeskDecisionPublic,
    DeskDecisionType,
    EditorAssignment,
    EditorAssignmentCreate,
    EditorAssignmentPublic,
    Paper,
    PaperAuthor,
    PaperPublic,
    PapersPublic,
    PaperSubmission,
    PaperVersion,
    Person,
    PersonRole,
    ReviewerAssignment,
    ReviewerAssignmentCreate,
    ReviewerAssignmentPublic,
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


# =============================================================================
# Editor Workflow Endpoints
# =============================================================================


@router.post("/{paper_id}/editor-assignment", response_model=EditorAssignmentPublic)
def assign_editor(
    *,
    session: SessionDep,
    current_editor: CurrentEditor,
    paper_id: uuid.UUID,
    assignment: EditorAssignmentCreate,
) -> Any:
    """Assign an editor to a paper. Only editors/admins can do this."""
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    editor_person = session.get(Person, assignment.editor_person_id)
    if not editor_person:
        raise HTTPException(status_code=400, detail="Editor person not found")
    if editor_person.role not in (PersonRole.editor, PersonRole.admin):
        raise HTTPException(status_code=400, detail="Person is not an editor")

    editor_assignment = EditorAssignment(
        paper_id=paper_id,
        editor_person_id=assignment.editor_person_id,
    )
    session.add(editor_assignment)
    session.commit()
    session.refresh(editor_assignment)
    return editor_assignment


@router.post("/{paper_id}/desk-decision", response_model=DeskDecisionPublic)
def make_desk_decision(
    *,
    session: SessionDep,
    current_editor: CurrentEditor,
    paper_id: uuid.UUID,
    decision: DeskDecisionCreate,
) -> Any:
    """Make a desk decision (proceed/reject) on a paper."""
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    existing = session.exec(
        select(DeskDecision).where(DeskDecision.paper_id == paper_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Desk decision already made")

    desk_decision = DeskDecision(
        paper_id=paper_id,
        decision=decision.decision,
        rationale=decision.rationale,
    )
    session.add(desk_decision)
    session.commit()
    session.refresh(desk_decision)
    return desk_decision


@router.post(
    "/{paper_id}/versions/{version_id}/reviewers",
    response_model=ReviewerAssignmentPublic,
)
def invite_reviewer(
    *,
    session: SessionDep,
    current_editor: CurrentEditor,
    paper_id: uuid.UUID,
    version_id: uuid.UUID,
    assignment: ReviewerAssignmentCreate,
) -> Any:
    """Invite a reviewer to review a paper version."""
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    version = session.get(PaperVersion, version_id)
    if not version or version.paper_id != paper_id:
        raise HTTPException(status_code=404, detail="Paper version not found")

    desk = session.exec(
        select(DeskDecision).where(DeskDecision.paper_id == paper_id)
    ).first()
    if not desk or desk.decision != DeskDecisionType.proceed:
        raise HTTPException(status_code=400, detail="Paper not approved for review")

    reviewer = session.get(Person, assignment.reviewer_person_id)
    if not reviewer:
        raise HTTPException(status_code=400, detail="Reviewer not found")
    if reviewer.role not in (PersonRole.reviewer, PersonRole.editor, PersonRole.admin):
        raise HTTPException(status_code=400, detail="Person cannot review papers")

    existing = session.exec(
        select(ReviewerAssignment).where(
            ReviewerAssignment.paper_version_id == version_id,
            ReviewerAssignment.reviewer_person_id == assignment.reviewer_person_id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Reviewer already assigned")

    reviewer_assignment = ReviewerAssignment(
        paper_version_id=version_id,
        reviewer_person_id=assignment.reviewer_person_id,
        identity_confidential=assignment.identity_confidential,
    )
    session.add(reviewer_assignment)
    session.commit()
    session.refresh(reviewer_assignment)
    return reviewer_assignment


@router.post("/{paper_id}/versions/{version_id}/decision", response_model=DecisionPublic)
def make_decision(
    *,
    session: SessionDep,
    current_editor: CurrentEditor,
    paper_id: uuid.UUID,
    version_id: uuid.UUID,
    decision: DecisionCreate,
) -> Any:
    """Make a final decision (accept/reject/revise) on a paper version."""
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    version = session.get(PaperVersion, version_id)
    if not version or version.paper_id != paper_id:
        raise HTTPException(status_code=404, detail="Paper version not found")

    existing = session.exec(
        select(Decision).where(Decision.paper_version_id == version_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Decision already made")

    final_decision = Decision(
        paper_version_id=version_id,
        decision=decision.decision,
        rationale=decision.rationale,
    )
    session.add(final_decision)
    session.commit()
    session.refresh(final_decision)
    return final_decision
