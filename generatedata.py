import csv 

data = [
    ['Barcode', 'Name', 'Price'],
    ['05000159461122', 'Snickers', '1'],
    ['5000159407236', 'Mars', '2'],
    ['5000159459228', 'Twix', '3'],
]

with open('products.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data)