import barcode
import argparse


def generate_barcodes(input_file: str) -> None:
    """Читает txt файлы и генеринует SVG штрих коды в кодировке Code128"""
    try:
        code128 = barcode.get_barcode_class("code128")
        with open(input_file, "r", encoding= "utf-8") as f:
            lines = f.readlines()
        for line_num, text in enumerate(lines, start=1):
            text = text.strip() 
            if not text:
                continue

            barcode_obj = code128(text)
            filename = f"barcode_{line_num}"
            barcode_obj.save(filename, text=text)
            print(f"Сгенерирован: {filename}.svg для текста: '{text}'")

    except FileNotFoundError:
        print(f"File {input_file} does not exist")


def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument(
        "--input",
        "-i",
        default="input.txt",
        help="Путь к файлу с входными данными",
    )

    args = parser.parse_args()
    generate_barcodes(args.input)


if __name__ == "__main__":
    main()
