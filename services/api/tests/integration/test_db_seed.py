"""Database seeding integration test: the real Pino Yard data (menu, hours and address from the restaurant)."""
import pytest
from sqlalchemy import select
from pino_yard.infrastructure.db.seed import seed_database
from pino_yard.infrastructure.db.models import (
    RestaurantModel, BranchModel, OpeningHourModel, MenuCategoryModel,
    ProductModel, ProductImageModel, PhysicalTableModel, TableQrTokenModel, UserModel
)


@pytest.mark.asyncio
async def test_seed_database_integration(db_session):
    await seed_database(db_session)

    # Restaurant: the site's facts only (no invented founding year)
    restaurant = (await db_session.execute(select(RestaurantModel))).scalar_one()
    assert restaurant.name_ar == "بينو يارد"
    assert restaurant.name_en == "Pino Yard"
    assert restaurant.phone == "+962 79 171 1118"
    assert "pinoyard.jo" in restaurant.about_ar and "pinoyard.jo" in restaurant.about_en

    # Branch: the one branch on Prince Tharwat Street, where the tables are
    branches = (await db_session.execute(select(BranchModel))).scalars().all()
    assert len(branches) == 1
    main = branches[0]
    assert main.is_demo_branch
    assert "الأمير ثروت" in main.name_ar and "الأمير ثروت" in main.address_ar
    assert main.name_en == "Pino Yard - Prince Tharwat Street" and main.phone == "+962 79 171 1118"

    # Opening hours: every day 08:00-02:00 (past midnight), with no special notes
    hours = (await db_session.execute(select(OpeningHourModel))).scalars().all()
    assert len(hours) == 7 and sorted(day.day_of_week for day in hours) == list(range(7))
    assert all((day.opens_at, day.closes_at) == ("08:00", "02:00") for day in hours)
    assert all(day.notes_ar is None and day.notes_en is None for day in hours)

    # Dine-in menu: 24 sections, 184 dishes at the menu's prices
    categories = (await db_session.execute(select(MenuCategoryModel).order_by(MenuCategoryModel.sort_order))).scalars().all()
    assert len(categories) == 24
    assert [c.name_en for c in categories[:3]] == ["Arabic Breakfast", "Western Breakfast", "Manaeesh"]
    assert categories[-1].name_ar == "أراجيل" and categories[-1].name_en == "Shisha"
    products = {p.name_ar: p for p in (await db_session.execute(select(ProductModel))).scalars().all()}
    assert len(products) == 184
    assert products["بيتزا بينو"].price_minor == 6500 and products["ستيك ريب آي"].price_minor == 21900
    assert products["قهوة تركية سنجل"].price_minor == 2750 and products["مياه صغيرة"].price_minor == 1000
    assert products["ساندويش دجاج كرنشي (حار)"].name_en == "Crunchy Chicken Sandwich (Spicy)"
    assert all(p.currency == "JOD" and p.is_available for p in products.values())

    # Details only where the menu gives them
    assert products["بيتزا مارغريتا"].description_en == "Pizza dough, tomato sauce and mozzarella cheese."
    assert "موزاريلا" in products["بيتزا مارغريتا"].description_ar
    assert products["حمص"].description_ar is None and products["شاي أحمر"].description_ar is None

    # The menu's dish photos: one per dish, set as its main photo
    images = (await db_session.execute(select(ProductImageModel))).scalars().all()
    assert len(images) == 184
    pizza = products["بيتزا بينو"]
    assert len([image for image in images if image.product_id == pizza.id]) == 1
    assert pizza.image_asset_url and pizza.image_asset_url.startswith(f"/api/v1/menu/products/{pizza.id}/images/")
    assert {image.product_id for image in images} == {p.id for p in products.values()}  # every dish has one

    # Tables (T1..T12) in the main branch
    tables = (await db_session.execute(select(PhysicalTableModel))).scalars().all()
    assert len(tables) == 12 and all(table.branch_id == main.id for table in tables)

    # QR codes are never seeded; an administrator creates unguessable ones per table.
    tokens = (await db_session.execute(select(TableQrTokenModel))).scalars().all()
    assert tokens == []

    # Verify Demo accounts
    users = (await db_session.execute(select(UserModel))).scalars().all()
    assert len(users) == 2
    emails = {u.email for u in users}
    assert "admin@pinoyard.com" in emails
    assert "customer@pinoyard.com" in emails
