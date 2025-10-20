import csv,os

def get_csv(filename):
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5


def create_overlay(data_dict : list[dict[str,str]], output_path : str):
    c = canvas.Canvas(output_path, pagesize=A5)
    for row in data_dict :
        c.drawString(float(row['Adjusted_X']), float(row['Adjusted_Y']) ,text=row["NAME"])
    c.save()

from PyPDF2 import PdfReader, PdfWriter

def merge_overlay(base_pdf_path, overlay_pdf_path, output_path):
    base = PdfReader(base_pdf_path)
    overlay = PdfReader(overlay_pdf_path)
    writer = PdfWriter()

    base_page = base.pages[0]
    overlay_page = overlay.pages[0]

    base_page.merge_page(overlay_page)
    writer.add_page(base_page)

    with open(output_path, "wb") as f:
        writer.write(f)


currentpath = os.path.dirname(os.path.abspath(__file__))
pdfpath = os.path.join(currentpath,'dist')
csv_data = os.path.join(pdfpath, "testcsv.csv")
form = os.path.join(pdfpath, "A5_Form1.pdf")
fill_form = os.path.join(pdfpath, "fill_form.pdf")
final = os.path.join(pdfpath, "final.pdf")

print(csv_data)
data = get_csv(csv_data)
create_overlay(data, fill_form)
merge_overlay(form, fill_form, final)
