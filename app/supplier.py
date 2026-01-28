import hashlib
import re

import httpx

from app.schemas import PartOffer
from app.settings import settings


class SupplierClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=15.0)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def brands(self, article: str) -> list[str]:
        article = article.strip()
        if not settings.supplier_api_base_url:
            raise RuntimeError("SUPPLIER_API_BASE_URL is not configured")
        _require_abstd_credentials()
        url = f"{settings.supplier_api_base_url.rstrip('/')}/api-brands"
        params = {"auth": _abstd_auth(), "article": article, "format": "json"}
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return [str(x) for x in data]
        raise RuntimeError("Unexpected brands response from supplier")

    async def search(
        self,
        article: str,
        *,
        brand: str | None = None,
        with_cross: bool = False,
        show_unavailable: bool = False,
    ) -> list[PartOffer]:
        article = article.strip()
        if not settings.supplier_api_base_url:
            raise RuntimeError("SUPPLIER_API_BASE_URL is not configured")
        _require_abstd_credentials()
        if settings.supplier_agreement_id is None:
            raise RuntimeError("SUPPLIER_AGREEMENT_ID is not configured")

        url = f"{settings.supplier_api_base_url.rstrip('/')}/api-search"
        params: dict[str, str] = {
            "auth": _abstd_auth(),
            "article": article,
            "agreement_id": str(settings.supplier_agreement_id),
            "with_cross": "1" if with_cross else "0",
            "show_unavailable": "1" if show_unavailable else "0",
            "format": "json",
        }
        if brand:
            params["brand"] = brand

        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
        status_val = str(payload.get("status", "")).strip()
        if status_val.upper() != "OK":
            raise RuntimeError(status_val or "Supplier returned error")

        offers: list[PartOffer] = []
        for item in payload.get("data", []) or []:
            offers.append(
                PartOffer(
                    supplier=str(item.get("warehouse_name") or "ABSTD"),
                    number=str(item.get("article") or article).strip().upper(),
                    name=str(item.get("product_name") or ""),
                    price=_to_float(item.get("price")),
                    currency=str(item.get("currency") or "RUB"),
                    qty=_to_int(item.get("quantity")),
                    delivery_days=_parse_delivery_days(
                        item.get("delivery_duration")
                    ),
                )
            )
        return offers


def _md5_lower(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest().lower()


def _abstd_auth() -> str:
    if settings.supplier_auth:
        return str(settings.supplier_auth).strip().lower()
    login = settings.supplier_login
    pw = settings.supplier_password
    return _md5_lower(login + _md5_lower(pw))


def _require_abstd_credentials() -> None:
    if settings.supplier_auth:
        return
    if not settings.supplier_login or not settings.supplier_password:
        raise RuntimeError(
            "SUPPLIER_LOGIN/SUPPLIER_PASSWORD are not configured"
        )


def _to_float(val) -> float:
    try:
        return float(str(val).replace(",", "."))
    except Exception:
        return 0.0


def _to_int(val) -> int:
    try:
        return int(float(str(val).replace(",", ".")))
    except Exception:
        return 0


_DELIVERY_RE = re.compile(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*$")


def _parse_delivery_days(val) -> int | None:
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    m = _DELIVERY_RE.match(s)
    if not m:
        return None
    # берем минимальный срок
    return int(m.group(1))
