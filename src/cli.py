import barcode
from barcode.writer import SVGWriter

# 1. Получаем класс штрих-кода Code128
code128_class = barcode.get_barcode_class("code128")

# 2. Создаем объект штрих-кода с нужными данными (например, строка "12345678")
# SVGWriter отвечает за отрисовку в формат SVG
barcode_obj = code128_class("12345678", writer=SVGWriter())

# 3. Сохраняем в файл (метод save создаст файл 'barcode.svg')
barcode_obj.save("barcode")