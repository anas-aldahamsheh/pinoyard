"""Initial Pino Yard data for an empty database.

Everything comes from Pino Yard Restaurant & Cafe's own pages: the dine-in menu (names,
prices, ingredients and the dish photos in ``seed_photos``) from its QR menu on bronqr.com,
and the address, phone and opening hours from pinoyard.com. ``seed_menu.json`` holds the menu
in both languages; the Arabic descriptions are translations of the restaurant's English ones,
with no ingredient added or left out, since the assistant answers allergy questions from them.
"""
import json
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pino_yard.infrastructure.db.models import (
    RestaurantModel, BranchModel, OpeningHourModel, MenuCategoryModel,
    ProductModel, ProductImageModel, PhysicalTableModel, UserModel
)
from pino_yard.domain.enums import UserRole, TableShape
from pino_yard.domain.money import jod_to_fils
from pino_yard.domain.units import units_to_json
from pino_yard.infrastructure.auth.passwords import hash_password
from pino_yard.infrastructure.media_store import media_store
from pino_yard.settings import settings


# Sign-ins for the automated tests only. Their passwords are published in this repository,
# so a real run (development or production) never creates them and disables them at
# startup if a database still has them: the only account there is ADMIN_EMAIL/ADMIN_PASSWORD.
DEMO_ACCOUNTS = (
    ("admin@pinoyard.com", "admin12345", UserRole.ADMIN),
    ("customer@pinoyard.com", "user12345", UserRole.USER),
)

SEED_PHOTOS = Path(__file__).with_name("seed_photos")

RESTAURANT = {
    "name_ar": "بينو يارد",
    "name_en": "Pino Yard",
    "about_ar": (
        "بينو يارد مطعم وكافيه في عمّان، شعاره \"Pine & dine\": تجربة مصمَّمة بين خشب الصنوبر والخضرة "
        "والجلسات المفتوحة. مطبخ عالمي من الأطباق الأوروبية والآسيوية والمتوسطية، وفطور عربي وغربي، "
        "وقهوة مختصة ومشروبات مميزة وأراجيل. الهابي تايم يومياً من الساعة 1 للساعة 4 العصر. "
        "تابعونا على إنستغرام: pinoyard.jo"
    ),
    "about_en": (
        "Pino Yard is a restaurant and cafe in Amman: \"Pine & dine, an experience by design\", among pine wood, "
        "greenery and open-air charm. International cuisine (modern European, Asian-inspired and Mediterranean "
        "plates), Arabic and western breakfast, specialty coffee, signature drinks and shisha. Happy Time daily "
        "from 1 PM to 4 PM. Follow us on Instagram: pinoyard.jo"
    ),
    "phone": "+962 79 171 1118",
}

# Every day 08:00 to 02:00 (past midnight).
OPENING_HOURS = tuple((day, "08:00", "02:00", None, None) for day in range(7))

# The one branch, where the tables are.
BRANCHES = (
    {
        "name_ar": "بينو يارد - شارع الأمير ثروت",
        "name_en": "Pino Yard - Prince Tharwat Street",
        "address_ar": "شارع الأمير ثروت، عمّان، الأردن",
        "address_en": "Prince Tharwat Street, Amman, Jordan",
        "phone": "+962 79 171 1118",
        "is_demo_branch": True,
    },
)

# [{name_ar, name_en, products: [{name_ar, name_en, description_ar, description_en, price, units, photo}]}]
# units: how the dish is counted (صحن، كاسة، حبة، فنجان، أرجيلة...), as the admin would set them.
MENU = json.loads(Path(__file__).with_name("seed_menu.json").read_text(encoding="utf-8"))


async def seed_demo_accounts(session: AsyncSession) -> None:
    if settings.ENVIRONMENT != "test":
        return
    for email, password, role in DEMO_ACCOUNTS:
        existing = (await session.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
        if not existing:
            session.add(UserModel(email=email, password_hash=hash_password(password), role=role, is_active=True))


def add_opening_hours(session: AsyncSession, branch: BranchModel) -> None:
    for day, opens, closes, notes_ar, notes_en in OPENING_HOURS:
        session.add(OpeningHourModel(branch_id=branch.id, day_of_week=day, opens_at=opens, closes_at=closes,
                                     notes_ar=notes_ar, notes_en=notes_en))


def add_photos(session: AsyncSession, product: ProductModel, photos: tuple) -> None:
    """The dish's photos from ``seed_photos``, saved like an admin upload (the first is the main one)."""
    store = media_store()
    sort_order = 0
    for name in photos:
        path = SEED_PHOTOS / name
        if not path.is_file():
            continue
        image_id = str(uuid.uuid4())
        session.add(ProductImageModel(id=image_id, product_id=product.id, content_type="image/jpeg",
                                      storage_key=store.save(path.read_bytes(), "image/jpeg"), sort_order=sort_order))
        if sort_order == 0:
            product.image_asset_url = f"/api/v1/menu/products/{product.id}/images/{image_id}"
        sort_order += 1


async def seed_database(session: AsyncSession) -> None:
    """Create the initial Pino Yard data on an empty database.

    Only adds what is missing; it never changes rows that already exist, so the
    administrator's edits (menu, hours, tables) survive every restart.
    """
    # 1. Test sign-in accounts (automated tests only)
    await seed_demo_accounts(session)

    # 2. Restaurant
    restaurant = (await session.execute(select(RestaurantModel))).scalar_one_or_none()
    if not restaurant:
        restaurant = RestaurantModel(**RESTAURANT)
        session.add(restaurant)
        await session.flush()

    # 3. Branches, each with its opening hours
    branches = (await session.execute(select(BranchModel).where(BranchModel.restaurant_id == restaurant.id))).scalars().all()
    if not branches:
        for details in BRANCHES:
            new_branch = BranchModel(restaurant_id=restaurant.id, **details)
            session.add(new_branch)
            await session.flush()
            add_opening_hours(session, new_branch)
        branches = (await session.execute(select(BranchModel).where(BranchModel.restaurant_id == restaurant.id))).scalars().all()
    # The tables belong to the branch the guests order from.
    branch = next((b for b in branches if b.is_demo_branch), branches[0])

    # 4. Dine-in menu: categories, dishes and their photos
    existing_cats = (await session.execute(select(MenuCategoryModel).where(MenuCategoryModel.restaurant_id == restaurant.id))).scalars().all()
    if not existing_cats:
        for category_order, category_data in enumerate(MENU, start=1):
            category = MenuCategoryModel(restaurant_id=restaurant.id, name_ar=category_data["name_ar"],
                                         name_en=category_data["name_en"], sort_order=category_order)
            session.add(category)
            await session.flush()
            for dish_order, dish in enumerate(category_data["products"]):
                product = ProductModel(
                    id=str(uuid.uuid4()),
                    category_id=category.id,
                    name_ar=dish["name_ar"],
                    name_en=dish["name_en"],
                    description_ar=dish["description_ar"],
                    description_en=dish["description_en"],
                    price_minor=jod_to_fils(dish["price"]),
                    units_json=units_to_json(dish.get("units") or []),
                    currency="JOD",
                    is_available=True,
                    sort_order=dish_order,
                )
                session.add(product)
                add_photos(session, product, (dish["photo"],))

    # 5. Tables T1 to T12. QR codes are never seeded: an administrator
    # creates an unguessable QR for each table from the Tables & QR page.
    existing_tables = (await session.execute(select(PhysicalTableModel).where(PhysicalTableModel.branch_id == branch.id))).scalars().all()
    if not existing_tables:
        # Where each table sits on the floor plan (apps/web/public/floor-plan-wide.webp), in percent:
        # the centre of its top, as projected by the render's camera.
        table_configs = [
            (f"T{row * 4 + col + 1}", (18.18, 30.99, 43.80, 56.61)[col], (34.59, 48.75, 62.90)[row], 0.0)
            for row in range(3) for col in range(4)
        ]
        for t_num, x, y, rot in table_configs:
            tbl = PhysicalTableModel(
                branch_id=branch.id,
                table_number=t_num,
                shape=TableShape.ROUND,
                seat_count=4,
                x_percent=x,
                y_percent=y,
                rotation_deg=rot,
                is_active=True
            )
            session.add(tbl)

    await session.commit()
