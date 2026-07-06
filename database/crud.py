"""
Reusable base standard CRUD abstractions. Handles low level mechanics,
exceptions encapsulation, and parameterized atomic execution.
"""

from typing import Type, List, Optional, Any, Generic, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DataError

from database.models import Base
from database.interfaces import IBaseCRUD
from database.exceptions import ConstraintViolationError, RecordNotFoundError, IOBDatabaseError

T = TypeVar('T', bound=Base)


class BaseCRUD(IBaseCRUD[T], Generic[T]):
    """Implements structural interface mappings over standard object lifecycles."""

    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, session: Session, entity: T) -> T:
        try:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity
        except IntegrityError as ex:
            session.rollback()
            raise ConstraintViolationError("Encountered integrity or validation check error during engine insert.", ex)
        except Exception as ex:
            session.rollback()
            raise IOBDatabaseError("System failure processing entity baseline save operations.", ex)

    def get_by_id(self, session: Session, ident: Any) -> Optional[T]:
        record = session.query(self.model).filter(self.model.id == ident).first()
        if not record:
            raise RecordNotFoundError(f"Identity key '{ident}' does not correspond to structural data records.")
        return record

    def get_all(self, session: Session, skip: int = 0, limit: int = 100) -> List[T]:
        return session.query(self.model).offset(skip).limit(limit).all()

    def update(self, session: Session, entity: T) -> T:
        try:
            merged = session.merge(entity)
            session.commit()
            return merged
        except IntegrityError as ex:
            session.rollback()
            raise ConstraintViolationError("Validation or unique index violation encountered during record merge execution.", ex)

    def delete(self, session: Session, ident: Any) -> bool:
        record = session.query(self.model).filter(self.model.id == ident).first()
        if not record:
            return False
        try:
            session.delete(record)
            session.commit()
            return True
        except Exception as ex:
            session.rollback()
            raise IOBDatabaseError("Unable to clean target row from structural physical files.", ex)
