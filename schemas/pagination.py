"""
Tipo genérico de respuesta paginada.

Uso:
    from schemas.pagination import PaginatedResponse
    return PaginatedResponse[MySchema](items=rows, total=n, page=page, page_size=size)
"""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(..., ge=0, description="Total de registros sin paginar")
    page: int = Field(..., ge=1, description="Página actual (1-based)")
    page_size: int = Field(..., ge=1, le=200, description="Registros por página")
    total_pages: int = Field(..., ge=0, description="Total de páginas")

    @classmethod
    def build(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        import math
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
