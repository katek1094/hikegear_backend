from .models import Profile, Brand, Category, Subcategory
from openpyxl import load_workbook


def xd():
    Brand.objects.all().delete()
    Subcategory.objects.all().delete()
    Category.objects.all().delete()
    wb = load_workbook('/home/kajetan/Desktop/reviews.xlsx', read_only=True)
    brands = wb['brands']
    bulk = []
    for x in range(40):
        data = brands[f'A{x + 1}'].value
        if data:
            bulk.append(Brand(name=data))
    Brand.objects.bulk_create(bulk)
    bulk = []
    categories = wb['categories']
    for x in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        for y in range(20):
            data = categories[f'{x}{y + 1}'].value
            if y == 0:
                print(data)
                cat = Category.objects.create(name=data)
            else:
                if data:
                    bulk.append(Subcategory(category=cat, name=data))
    Subcategory.objects.bulk_create(bulk)

# python manage.py shell
# from app.scripts import xd
