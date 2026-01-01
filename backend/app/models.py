import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from typing import Optional


# =============================================================================
# Person - Public profile for authors, reviewers, editors
# Separate from User (login account). Someone can be a paper author without
# having a login account (placeholder Person with email, linked on first login).
# =============================================================================


class PersonRole(str, Enum):
    """Role determines what actions a person can take in the journal system."""
    researcher = "researcher"  # Can submit papers, be listed as author
    reviewer = "reviewer"      # Can be assigned to review papers
    editor = "editor"          # Can make desk decisions, assign reviewers, make final decisions
    admin = "admin"            # Full system access


class PersonBase(SQLModel):
    display_name: str = Field(max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255, index=True)
    orcid: str | None = Field(default=None, max_length=19)  # Format: 0000-0000-0000-0000
    role: PersonRole = Field(default=PersonRole.researcher)


class PersonCreate(PersonBase):
    pass


class PersonUpdate(SQLModel):
    display_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    orcid: str | None = Field(default=None, max_length=19)
    role: PersonRole | None = None


class Person(PersonBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: list["User"] = Relationship(back_populates="person")


class PersonPublic(PersonBase):
    id: uuid.UUID
    created_at: datetime


class PersonsPublic(SQLModel):
    data: list[PersonPublic]
    count: int


# =============================================================================
# Paper - A submission to the journal
# =============================================================================


class PaperBase(SQLModel):
    title: str = Field(min_length=1, max_length=500)
    abstract: str | None = Field(default=None, max_length=10000)


class PaperCreate(PaperBase):
    resubmission_of_paper_id: uuid.UUID | None = None


class PaperUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    abstract: str | None = Field(default=None, max_length=10000)


class Paper(PaperBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resubmission_of_paper_id: uuid.UUID | None = Field(
        default=None, foreign_key="paper.id"
    )
    versions: list["PaperVersion"] = Relationship(back_populates="paper")
    authors: list["PaperAuthor"] = Relationship(back_populates="paper")


class PaperPublic(PaperBase):
    id: uuid.UUID
    created_at: datetime
    resubmission_of_paper_id: uuid.UUID | None


class PapersPublic(SQLModel):
    data: list[PaperPublic]
    count: int


# =============================================================================
# PaperVersion - Each revision of a paper
# =============================================================================


class PaperVersionBase(SQLModel):
    version_number: int = Field(ge=1)
    pdf_url: str = Field(max_length=2000)


class PaperVersionCreate(PaperVersionBase):
    paper_id: uuid.UUID


class PaperVersion(PaperVersionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    paper_id: uuid.UUID = Field(foreign_key="paper.id")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    paper: Paper = Relationship(back_populates="versions")


class PaperVersionPublic(PaperVersionBase):
    id: uuid.UUID
    paper_id: uuid.UUID
    submitted_at: datetime


# =============================================================================
# PaperAuthor - Links authors (Person) to papers with ordering
# =============================================================================


class PaperAuthorBase(SQLModel):
    author_position: int = Field(ge=1)
    is_corresponding: bool = Field(default=False)


class PaperAuthorCreate(PaperAuthorBase):
    paper_id: uuid.UUID
    person_id: uuid.UUID


class PaperAuthor(PaperAuthorBase, table=True):
    paper_id: uuid.UUID = Field(foreign_key="paper.id", primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.id", primary_key=True)
    paper: Paper = Relationship(back_populates="authors")
    person: Person = Relationship()


class PaperAuthorPublic(PaperAuthorBase):
    paper_id: uuid.UUID
    person_id: uuid.UUID


# =============================================================================
# User - Login account (authentication)
# Linked to Person for public profile. Template originally called this "User",
# will rename to "LoginAccount" after vertical slice is working.
# =============================================================================


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    person_id: uuid.UUID | None = Field(default=None, foreign_key="person.id")
    person: Person | None = Relationship(back_populates="user")
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
