from __future__ import annotations

import functools
import operator

from typing import TYPE_CHECKING, Iterable, TypeAlias, TypeVar

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Model, Q, QuerySet
from django.utils.encoding import force_str

if TYPE_CHECKING:  # pragma: no cover
    _T = TypeVar("_T", bound=Model)
    _QuerySet: TypeAlias = QuerySet[_T]
else:
    _QuerySet = object


class SearchQuerySetMixin(_QuerySet):
    """Provides standard search interface for models supporting search vector and ranking.

    Adds a `search` method to automatically resolve simple PostgreSQL search vector queries.

    Attributes:
        search_vectors: SearchVector fields and ranks (if multiple)
        search_vector_field: single SearchVectorField
        search_rank: SearchRank field for ordering
        search_type: PostgreSQL search type
    """

    search_vectors: list[tuple[str, str]] = []
    search_vector_field: str = "search_vector"
    search_rank: str = "rank"
    search_type: str = "websearch"

    def search(self: _QuerySet, search_term: str) -> _QuerySet:
        """Returns result of search."""
        if not search_term:
            return self.none()

        query = SearchQuery(force_str(search_term), search_type=self.search_type)

        return self.annotate(**dict(self._search_ranks(query))).filter(
            functools.reduce(operator.or_, self._search_filters(query))
        )

    def _search_filters(self, query: SearchQuery) -> Iterable[Q]:

        if self.search_vectors:
            for field, _ in self.search_vectors:
                yield Q(**{field: query})
        else:
            yield Q(**{self.search_vector_field: query})

    def _search_ranks(self, query: SearchQuery) -> Iterable[tuple[str, SearchRank]]:
        if not self.search_vectors:
            yield self.search_rank, SearchRank(F(self.search_vector_field), query=query)
            return

        combined: list[F] = []

        for field, rank in self.search_vectors:
            yield rank, SearchRank(F(field), query=query)

            combined.append(F(rank))

        yield self.search_rank, functools.reduce(operator.add, combined)