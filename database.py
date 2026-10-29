from sqlalchemy import create_engine, Table, String, MetaData, Column, Integer
from sqlalchemy import insert 
import csv

def add_data(barcode, name, price):
    statement = insert(inventory_table).values(barcode=barcode, name=name, price=price)
    with engine.connect() as connection:
        connection.execute(statement)
        connection.commit()

def read_csv_and_insert_data():
    with open('products.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row
        for row in reader:
            barcode, name, price = row
            add_data(int(barcode), name, int(price))


metadata_object = MetaData()

inventory_table = Table(
    "inventory",
    metadata_object,
    Column("barcode", Integer, primary_key=True),
    Column("name", String),
    Column("price", Integer)
)

engine = create_engine("sqlite:///inventory.db", echo=True)

metadata_object.create_all(engine)
read_csv_and_insert_data()

