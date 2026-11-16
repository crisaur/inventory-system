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


def upsert_product(sku: int, name: str, price: float) -> dict:
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
                return {"SKU": sku, "Name": name, "Status": "UPDATED", "Old Price": old_price, "New Price": price}
            else:
                return {"SKU": sku, "Name": name, "Status": "SKIPPED", "Old Price": old_price, "New Price": price}
        else:
            connection.execute(
                insert(inventory_table).values(sku=sku, name=name, price=price)
            )
            return {"SKU": sku, "Name": name, "Status": "ADDED", "Old Price": None, "New Price": price}


def read_csv_and_insert_data(csv_path: str = "products.csv"):
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            sku, name, price = row
            upsert_product(int(sku), name.strip(), float(price))


if __name__ == "__main__":
    read_csv_and_insert_data()