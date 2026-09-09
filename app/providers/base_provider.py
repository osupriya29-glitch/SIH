"""
Base class for all external data providers.

Providers are the ONLY layer allowed to call external APIs (see project
architecture rule: agents never call external APIs directly). Every
provider method should:
  - use the shared httpx.AsyncClient passed in at construction
  - raise ProviderError (never a raw httpx exception) on failure
  - return provider-native data — normalization into the common schema
    happens in the service layer (Phase 9), not here
"""
import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class ProviderError(Exception):
    """
    Raised whenever a provider cannot return real data.

    provider: short provider name, e.g. "IMD"
    detail: human-readable reason
    status_code: upstream HTTP status if there was one, else None
    """

    def __init__(
        self,
        provider: str,
        detail: str,
        status_code: int | None = None,
        is_timeout: bool = False,
    ):
        self.provider = provider
        self.detail = detail
        self.status_code = status_code
        self.is_timeout = is_timeout
        super().__init__(f"[{provider}] {detail}")


class ProviderNotConfigured(Exception):
    """
    Raised when a provider needs configuration (typically an API key) that
    hasn't been set, rather than sending a request that will just fail
    upstream. Distinct from ProviderError: this is a deployment/config
    issue on our side, not an upstream failure.
    """

    def __init__(self, provider: str, detail: str):
        self.provider = provider
        self.detail = detail
        super().__init__(f"[{provider}] {detail}")


class BaseProvider:
    provider_name: str = "base"

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def _get_text(self, url: str, params: dict | None = None, headers: dict | None = None) -> str:
        """GET a URL and return raw text (for plain-text endpoints like NDBC's realtime2 files)."""
        response = await self._send("GET", url, params=params, headers=headers)
        return response.text

    async def _get(self, url: str, params: dict | None = None, headers: dict | None = None) -> dict | list:
        """
        GET a URL and return parsed JSON, or raise ProviderError.
        Never fabricates a fallback value on failure.
        """
        response = await self._send("GET", url, params=params, headers=headers)
        return self._parse_json(response, url)

    async def _post_form(self, url: str, data: dict) -> dict | list | str:
        """
        POST form-encoded data and return parsed JSON when the response is
        JSON, otherwise the raw response text (some endpoints, like NASA's
        file_search, can return plain-text listings depending on the
        request). Never fabricates a fallback value on failure.
        """
        response = await self._send("POST", url, data=data)
        try:
            return response.json()
        except ValueError:
            return response.text

    async def _send(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            response = await self._client.request(method, url, **kwargs)
        except httpx.TimeoutException as exc:
            raise ProviderError(self.provider_name, "Request timed out", is_timeout=True) from exc
        except httpx.RequestError as exc:
            raise ProviderError(self.provider_name, f"Request failed: {exc}") from exc

        if response.status_code >= 400:
            logger.warning(
                "%s returned HTTP %s for %s", self.provider_name, response.status_code, url
            )
            raise ProviderError(
                self.provider_name,
                f"Upstream returned HTTP {response.status_code}",
                status_code=response.status_code,
            )
        return response

    def _parse_json(self, response: httpx.Response, url: str) -> dict | list:
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(self.provider_name, "Upstream returned malformed JSON") from exc
