import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Review,
    ReviewCreate,
    ReviewerAssignment,
    ReviewerAssignmentPublic,
    ReviewerAssignmentsPublic,
    ReviewerAssignmentStatus,
    ReviewerAssignmentUpdate,
    ReviewerAssignmentWithPaper,
    ReviewPublic,
)

router = APIRouter(prefix="/reviewer-assignments", tags=["reviewer-assignments"])


@router.get("/", response_model=ReviewerAssignmentsPublic)
def list_my_assignments(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """List current user's reviewer assignments."""
    if not current_user.person_id:
        raise HTTPException(status_code=403, detail="User has no person profile")

    assignments = session.exec(
        select(ReviewerAssignment)
        .where(ReviewerAssignment.reviewer_person_id == current_user.person_id)
        .order_by(ReviewerAssignment.invited_at.desc())
    ).all()

    result = []
    for a in assignments:
        paper_version = a.paper_version
        paper = paper_version.paper
        result.append(
            ReviewerAssignmentWithPaper(
                id=a.id,
                paper_version_id=a.paper_version_id,
                reviewer_person_id=a.reviewer_person_id,
                status=a.status,
                invited_at=a.invited_at,
                identity_confidential=a.identity_confidential,
                paper_title=paper.title,
                paper_id=paper.id,
            )
        )

    return ReviewerAssignmentsPublic(data=result, count=len(result))


@router.patch("/{assignment_id}", response_model=ReviewerAssignmentPublic)
def respond_to_invitation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    assignment_id: uuid.UUID,
    update: ReviewerAssignmentUpdate,
) -> Any:
    """Reviewer accepts or declines an invitation."""
    assignment = session.get(ReviewerAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if not current_user.person_id:
        raise HTTPException(status_code=403, detail="User has no person profile")
    if assignment.reviewer_person_id != current_user.person_id:
        raise HTTPException(status_code=403, detail="Not your assignment")

    if assignment.status != ReviewerAssignmentStatus.invited:
        raise HTTPException(
            status_code=400, detail="Can only respond to pending invitations"
        )

    if update.status not in (
        ReviewerAssignmentStatus.accepted,
        ReviewerAssignmentStatus.declined,
    ):
        raise HTTPException(
            status_code=400, detail="Status must be accepted or declined"
        )

    assignment.status = update.status
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment


@router.post("/{assignment_id}/review", response_model=ReviewPublic)
def submit_review(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    assignment_id: uuid.UUID,
    review: ReviewCreate,
) -> Any:
    """Reviewer submits their review."""
    assignment = session.get(ReviewerAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if not current_user.person_id:
        raise HTTPException(status_code=403, detail="User has no person profile")
    if assignment.reviewer_person_id != current_user.person_id:
        raise HTTPException(status_code=403, detail="Not your assignment")

    if assignment.status != ReviewerAssignmentStatus.accepted:
        raise HTTPException(
            status_code=400, detail="Must accept invitation before submitting review"
        )

    existing = session.exec(
        select(Review).where(Review.assignment_id == assignment_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Review already submitted")

    new_review = Review(
        assignment_id=assignment_id,
        content=review.content,
    )
    session.add(new_review)

    assignment.status = ReviewerAssignmentStatus.completed
    session.add(assignment)

    session.commit()
    session.refresh(new_review)
    return new_review
