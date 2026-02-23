
import openapi_pydantic as oa

from globus_registered_api.config import RegisteredAPIConfig


class InjectBaseUrl:
    def __init__(self, config: RegisteredAPIConfig):
        self._config = config

    def mutate(self, schema: oa.OpenAPI) -> None:
        schema.servers = [oa.Server(url=self._config.core.base_url)]

