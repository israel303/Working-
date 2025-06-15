from PIL import Image
import fitz  # PyMuPDF
import os

def save_default_thumbnail(image_path: str, save_path: str):
    img = Image.open(image_path)
    img.save(save_path)

def apply_thumbnail(input_file: str, output_file: str, thumbnail_path: str) -> bool:
    try:
        ext = os.path.splitext(input_file)[-1].lower()
        if ext == ".pdf":
            return _set_pdf_thumbnail(input_file, output_file, thumbnail_path)
        elif ext == ".epub":
            from shutil import copyfile
            copyfile(input_file, output_file)
            return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def _set_pdf_thumbnail(input_file: str, output_file: str, thumbnail_path: str) -> bool:
    doc = fitz.open(input_file)
    img = open(thumbnail_path, "rb").read()
    doc.set_metadata({'title': 'Thumbnail Added'})
    doc[0].insert_image(doc[0].rect, stream=img)
    doc.save(output_file)
    return True