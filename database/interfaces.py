"""
Abstract contract definitions dictating constraints for the structural operations pipeline.
"""

from typing import Generic, TypeVar, List, Optional, Any, Dict

T = TypeVar('T')


class IBaseCRUD(Generic[T]):
    """Enforces common interaction paradigms across standard storage access drivers."""
    def create(self, session: Any, entity: T) -> T: raise NotImplementedError
    def get_by_id(self, session: Any, ident: Any) -> Optional[T]: raise NotImplementedError
    def get_all(self, session: Any, skip: int = 0, limit: int = 100) -> List[T]: raise NotImplementedError
    def update(self, session: Any, entity: T) -> T: raise NotImplementedError
    def delete(self, session: Any, ident: Any) -> bool: raise NotImplementedError


class IRepository(Generic[T]):
    """Defines atomic semantic abstraction specifications separating database tasks from business rules."""
    def find_by_id(self, session: Any, id_val: Any) -> Optional[T]: raise NotImplementedError
    def save(self, session: Any, entity: T) -> T: raise NotImplementedError
    def remove(self, session: Any, id_val: Any) -> bool: raise NotImplementedError
