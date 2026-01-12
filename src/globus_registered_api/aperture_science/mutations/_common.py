import typing as t

class SchemaMutation(t.Protocol):

    def mutate(self, openapi_schema: dict[str, t.Any]) -> None:
        ...
