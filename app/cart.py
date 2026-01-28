from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CartItem


async def list_cart(db: AsyncSession, user_id: int) -> list[CartItem]:
    res = await db.execute(select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.id.desc()))
    return list(res.scalars().all())


async def add_to_cart(
    db: AsyncSession,
    *,
    user_id: int,
    supplier: str,
    number: str,
    name: str,
    price: float,
    currency: str,
    delivery_days: int | None,
    quantity: int = 1,
) -> CartItem:
    item = CartItem(
        user_id=user_id,
        supplier=supplier,
        number=number.strip().upper(),
        name=name,
        price=price,
        currency=currency,
        delivery_days=delivery_days,
        quantity=max(1, int(quantity)),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def remove_from_cart(db: AsyncSession, *, user_id: int, item_id: int) -> None:
    await db.execute(delete(CartItem).where(CartItem.user_id == user_id, CartItem.id == item_id))
    await db.commit()


async def clear_cart(db: AsyncSession, *, user_id: int) -> None:
    await db.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await db.commit()

