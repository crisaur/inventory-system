from sqlalchemy import create_engine, Table, String, MetaData, Column, Integer
from sqlalchemy import text
import csv

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

