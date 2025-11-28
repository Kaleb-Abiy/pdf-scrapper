import pdfplumber
import sys
from pathlib import Path

def crop_doc(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page1 = pdf.pages[0]
        texts = []
        next_school = 35
        x1, top, x2, bottom = 13, 165, 780, 200
        bbox = page1.crop((x1,top,x2,bottom))
        lines= bbox.extract_text_lines()
        for l in lines:
            print(l.get('text'))
        nextbox = page1.crop((x1, bottom, x2, bottom+next_school))
        lines = nextbox.extract_text_lines()

        for l in lines:
            print(l.get('text'))
     

def get_image(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page1 = pdf.pages[0]
        im = page1.to_image()

        im.show()


def main():
    if not len(sys.argv) < 2:
        pdf_path = sys.argv[1]

        if not Path(pdf_path).exists():
            sys.exit(1)
        
        # get_image(pdf_path)
        crop_doc(pdf_path)

main()