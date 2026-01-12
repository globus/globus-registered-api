from pathlib import Path

SEARCH_CONFIG = {
    # Load the OpenAPI spec from the specifications directory
    "openapi_uri": str(
        Path(__file__).parent / "specifications" / "search.openapi.json"
    ),
    "globus_auth": {}
}
