from openpyxl import load_workbook
from rest_framework.exceptions import ValidationError
from .. import constants


def validate_excel_file(excel_file):
    try:
        wb = load_workbook(excel_file)
    except KeyError:
        raise ValidationError({'excel': 'bad format, file must have .xlsx extension'})
    data = wb.active['A:C']
    if len(data[0]) > 2000:
        raise ValidationError({'excel': 'too many items'})
    if len(data[0]) == 0:
        raise ValidationError({'excel': 'no items provided'})
    return data


def new_my_gear_cat_id(gear_list):
    ids = []
    for cat in gear_list:
        ids.append(cat['id'])
    for x in range(1000):
        if x not in ids:
            return x
    return False


def scrape_data_from_excel(excel_file, private_gear):
    data = validate_excel_file(excel_file)

    items_ids = []
    for cat in private_gear:
        for item in cat['items']:
            items_ids.append(item['id'])

    new_categories = [{
        'name': 'importowane z pliku excel',
        'items': [],
        'id': new_my_gear_cat_id(private_gear)
    }]

    for (name, description, weight) in zip(data[0], data[1], data[2]):
        if name.value == 'kategoria':
            new_id = new_my_gear_cat_id(private_gear + new_categories)
            if not new_id:
                raise ValidationError({'excel': "can't find new id for category"})
            new_categories.append({'name': description.value, 'items': [], 'id': new_id})
        else:
            if name.value or description.value:
                final_id = None
                final_name = ""
                final_description = ""
                final_weight = 0

                for x in range(10000):
                    if x not in items_ids:
                        items_ids.append(x)
                        final_id = x
                        break
                if isinstance(name.value, str):
                    final_name = name.value[:constants.item_max_name_len]
                if isinstance(description.value, str):
                    final_description = description.value[:constants.item_max_description_len]
                if isinstance(weight.value, int):
                    if weight.value <= constants.item_max_weight:
                        final_weight = weight.value
                    else:
                        final_weight = constants.item_max_weight

                new_categories[-1]['items'].append({'name': final_name,
                                                    'description': final_description,
                                                    'weight': final_weight,
                                                    "id": final_id})
    return {'private_gear': private_gear + new_categories}



