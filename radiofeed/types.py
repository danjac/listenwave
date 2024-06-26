from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib import admin
    from django.db.models import Model, QuerySet
    from django.http import HttpRequest, HttpResponse
    from mypy_extensions import Arg, KwArg, VarArg

    T_Model = TypeVar("T_Model", bound=Model)
    T_QuerySet: TypeAlias = QuerySet[T_Model]
    T_ModelAdmin: TypeAlias = admin.ModelAdmin
    HttpRequestResponse: TypeAlias = Callable[
        [Arg(HttpRequest, "request"), VarArg(Any), KwArg(Any)],
        HttpResponse,
    ]

else:
    T_Model = object
    T_ModelAdmin = object
    T_QuerySet = object

    HttpRequestResponse: TypeAlias = Callable
