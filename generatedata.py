import csv 

data = [
    ['Barcode', 'Name', 'Price'],
    ['123456789012', 'Product A', '10.99'],
    ['987654321098', 'Product B', '15.49'],
    ['456789012345', 'Product C', '7.99'],
]

with open('products.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data)