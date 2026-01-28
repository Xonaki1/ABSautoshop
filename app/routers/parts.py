from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_current_user
from app.schemas import SearchResponse
from app.supplier import SupplierClient

router = APIRouter(prefix="/api/parts", tags=["parts"])


@router.get("/search", response_model=SearchResponse)
async def search_parts(
    number: str,
    brand: str | None = None,
    with_cross: int = 0,
    show_unavailable: int = 0,
    _user=Depends(get_current_user),
):
    client = SupplierClient()
    try:
        offers = await client.search(
            number,
            brand=brand,
            with_cross=bool(with_cross),
            show_unavailable=bool(show_unavailable),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Supplier error: {e}") from e
    finally:
        await client.aclose()
    return SearchResponse(number=number.strip().upper(), offers=offers)


@router.get("/brands")
async def brands(article: str, _user=Depends(get_current_user)):
    client = SupplierClient()
    try:
        res = await client.brands(article)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Supplier error: {e}") from e
    finally:
        await client.aclose()
    return res

