import csv 

data = [
    ['SKU', 'Name', 'Price'],
    ['297899', 'Cad Drinking Hot Choc', '1.00'],
    ['324317', 'McV Dark Choc Digs', '1.00'],
    ['306537', 'Fanta Lemon', '1.00'],
]

with open('products.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data)