from __future__ import annotations

import functools
import operator

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import connections
from django.db.models import F, Model, Q, QuerySet
from django.utils.encoding import force_str


class FastCountMixin:
    """Provides faster alternative to COUNT for very large tables, using PostgreSQL retuple SELECT.

    Attributes:
        fast_count_row_limit (int): max number of rows before switching from SELECT COUNT to reltuples.
    """

    fast_count_row_limit: int = 1000

    def count(self) -> int:
        """Does optimized COUNT.

        If query contains WHERE, DISTINCT or GROUP BY, or number of rows under `fast_count_row_limit`, returns standard SELECT COUNT.

        Returns:
            number of rows
        """
        if self._query.group_by or self._query.where or self._query.distinct:
            return super().count()
        if (
            count := get_reltuple_count(self.db, self.model._meta.db_table)
        ) > self.fast_count_row_limit:
            return count
        # exact count for small tables
        return super().count()


class SearchMixin:
    """Provides standard search interface for models supporting search vector and ranking.

    Adds a `search` method to automatically resolve simple PostgreSQL search vector queries.

    Attributes:
        search_vectors: SearchVector fields (if multiple)
        search_vector_field: single SearchVectorField
        search_rank: SearchRank field for ordering
        search_type: PostgreSQL search type
    """

    search_vectors: list[tuple[str, str]] = []
    search_vector_field: str = "search_vector"
    search_rank: str = "rank"
    search_type: str = "websearch"

    def search(self, search_term: str) -> QuerySet[Model]:
        """Returns result of search."""
        if not search_term:
            return self.none()

        query = SearchQuery(force_str(search_term), search_type=self.search_type)

        ranks: dict[str, SearchRank] = {}
        filters: list[Q] = []

        if self.search_vectors:

            combined_rank: list[F] = []

            for field, rank in self.search_vectors:
                ranks[rank] = SearchRank(F(field), query=query)
                combined_rank.append(F(rank))
                filters.append(Q(**{field: query}))

            ranks[self.search_rank] = functools.reduce(operator.add, combined_rank)

        else:
            ranks[self.search_rank] = SearchRank(
                F(self.search_vector_field), query=query
            )
            filters.append(Q(**{self.search_vector_field: query}))

        return self.annotate(**ranks).filter(functools.reduce(operator.or_, filters))


def get_reltuple_count(db: str, table: str) -> int:
    """Returns result of SELECT reltuples.

    Args:
        db: database name
        table: table name

    Returns:
        number of rows
    """
    cursor = connections[db].cursor()
    cursor.execute("SELECT reltuples FROM pg_class WHERE relname = %s", [table])
    return int(cursor.fetchone()[0])
