import csv
from sqlalchemy import create_engine, Table, String, MetaData, Column, Integer, Float, select, update
from sqlalchemy.dialects.sqlite import insert

metadata_object = MetaData()

inventory_table = Table(
    "inventory",
    metadata_object,
    Column("sku", Integer, primary_key=True),
    Column("name", String),
    Column("price", Float)
)

engine = create_engine("sqlite:///inventory.db", echo=False)
metadata_object.create_all(engine)


def upsert_product(sku: int, name: str, price: float):
    """
    Searches inventory.db by SKU:
    - If SKU exists and new price > current price -> updates the price
    - If SKU exists and new price <= current price -> skips update
    - If SKU is new -> inserts the new product
    """
    with engine.begin() as connection:
        existing = connection.execute(
            select(inventory_table.c.price).where(inventory_table.c.sku == sku)
        ).first()

        if existing is not None:
            old_price = existing.price
            if price > old_price:
                connection.execute(
                    update(inventory_table)
                    .where(inventory_table.c.sku == sku)
                    .values(price=price)
                )
                print(f"[UPDATED] SKU {sku} ({name}): £{old_price:.2f} -> £{price:.2f}")
            else:
                print(f"[SKIPPED] SKU {sku} ({name}): new price £{price:.2f} is not higher than £{old_price:.2f}")
        else:
            connection.execute(
                insert(inventory_table).values(sku=sku, name=name, price=price)
            )
            print(f"[ADDED] SKU {sku} ({name}): £{price:.2f}")


def read_csv_and_insert_data(csv_path: str = "products.csv"):
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            sku, name, price = row
            upsert_product(int(sku), name.strip(), float(price))


if __name__ == "__main__":
    read_csv_and_insert_data()