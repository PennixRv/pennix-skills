"""Run explicitly with the managed document Python after system dependencies exist.

Creates synthetic fixtures under a new temporary directory; never reads user files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from openpyxl import Workbook, load_workbook
from PIL import Image, ImageDraw, ImageFont
import pdfplumber
from pdf2image import convert_from_path
from pptx import Presentation
from pptx.util import Inches
from pypdf import PdfReader
import pytesseract

ROOT = Path(__file__).resolve().parents[1]


def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError(f"{args[0]} failed: {result.stderr}")
    return result.stdout


def convert(source, kind, directory, skill="docx"):
    directory.mkdir(parents=True, exist_ok=True)
    run([sys.executable, ROOT / "skills" / skill / "scripts/office/soffice.py",
         "--headless", "--convert-to", kind, "--outdir", directory, source])
    result = directory / (source.stem + "." + kind.split(":")[0])
    assert result.is_file(), f"LibreOffice returned without output: {result}"
    return result


def fixtures(directory):
    word = directory / "sample.docx"
    w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    document = f'''<w:document xmlns:w="{w}"><w:body>
<w:p><w:r><w:t>文档阅读测试 Document reading</w:t></w:r></w:p>
<w:tbl><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="8"/><w:left w:val="single" w:sz="8"/><w:bottom w:val="single" w:sz="8"/><w:right w:val="single" w:sz="8"/><w:insideH w:val="single" w:sz="8"/><w:insideV w:val="single" w:sz="8"/></w:tblBorders></w:tblPr><w:tblGrid><w:gridCol w:w="3000"/><w:gridCol w:w="3000"/></w:tblGrid>
<w:tr><w:tc><w:p><w:r><w:t>Item</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Count</w:t></w:r></w:p></w:tc></w:tr>
<w:tr><w:tc><w:p><w:r><w:t>Alpha</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>5</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
<w:p><w:r><w:br w:type="page"/></w:r></w:p><w:p><w:r><w:t>第二页 Summary</w:t></w:r></w:p>
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>'''
    with zipfile.ZipFile(word, "w") as bundle:
        bundle.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        bundle.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        bundle.writestr("word/document.xml", document)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "汇总"
    sheet.append([2, "中文数量"])
    sheet.append([3])
    sheet["A3"] = "=SUM(A1:A2)"
    sheet["A4"] = "=A3*2"
    workbook.create_sheet("说明")["A1"] = "公式与缓存分别读取"
    excel = directory / "sample.xlsx"
    workbook.save(excel)
    with zipfile.ZipFile(excel) as bundle:
        entries = {name: bundle.read(name) for name in bundle.namelist()}
    entries["xl/worksheets/sheet1.xml"] = entries["xl/worksheets/sheet1.xml"].replace(
        b"<f>SUM(A1:A2)</f><v></v>", b"<f>SUM(A1:A2)</f><v>5</v>")
    with zipfile.ZipFile(excel, "w") as bundle:
        for name, content in entries.items():
            bundle.writestr(name, content)
    presentation = Presentation()
    for number, title in enumerate(("第一项 Overview", "第二项 Results"), 1):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1)).text = title
        slide.notes_slide.notes_text_frame.text = f"讲者备注 Note {number}"
    powerpoint = directory / "sample.pptx"
    presentation.save(powerpoint)
    return word, excel, powerpoint


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    directory = Path(args.output_dir).absolute()
    if Path(tempfile.gettempdir()) not in directory.parents or directory.exists() or directory.is_symlink():
        parser.error("output must be a new directory below the system temporary directory")
    directory.mkdir(parents=True, mode=0o700)
    originals = fixtures(directory)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in originals}
    word, excel, powerpoint = originals
    text = run(["pandoc", "-t", "markdown", word])
    assert "文档阅读测试" in text and "Alpha" in text and "5" in text
    formulas = load_workbook(excel, read_only=True, data_only=False, keep_links=False)
    values = load_workbook(excel, read_only=True, data_only=True, keep_links=False)
    assert formulas.sheetnames == ["汇总", "说明"]
    assert formulas["汇总"]["A3"].value == "=SUM(A1:A2)" and values["汇总"]["A3"].value == 5
    assert formulas["汇总"]["A4"].value == "=A3*2" and values["汇总"]["A4"].value is None
    formulas.close(); values.close()
    for source, expected in ((excel, "中文数量"), (powerpoint, "Note 2")):
        extracted = run([str(Path(sys.executable).parent / "markitdown"), source])
        assert expected in extracted, extracted
        if source == powerpoint:
            assert extracted.index("Overview") < extracted.index("Results")
    pdf = convert(word, "pdf", directory / "render")
    reader = PdfReader(pdf)
    assert len(reader.pages) == 2
    assert "Alpha" in reader.pages[0].extract_text() and "Summary" in reader.pages[1].extract_text()
    with pdfplumber.open(pdf) as document:
        tables = document.pages[0].extract_tables()
        assert any("Alpha" in str(table) and "5" in str(table) for table in tables), tables
    pages = convert_from_path(pdf, dpi=80)
    assert len(pages) == 2 and min(pages[0].size) > 500
    slide_pdf = convert(powerpoint, "pdf", directory / "slides", "pptx")
    assert len(convert_from_path(slide_pdf, dpi=60)) == 2
    font = run(["fc-match", "-f", "%{file}", "Noto Sans CJK SC"]).strip()
    image = Image.new("RGB", (1800, 500), "white")
    ImageDraw.Draw(image).text((80, 120), "文档阅读测试 OCR 123", fill="black", font=ImageFont.truetype(font, 88))
    scan = directory / "scan.pdf"
    image.save(scan, "PDF", resolution=180)
    assert not (PdfReader(scan).pages[0].extract_text() or "").strip()
    ocr = pytesseract.image_to_string(convert_from_path(scan, dpi=180)[0], lang="chi_sim+eng")
    assert "文档" in ocr and "123" in ocr, ocr
    for source, legacy, modern, skill in ((word, "doc:MS Word 97", "docx", "docx"),
                                           (powerpoint, "ppt:MS PowerPoint 97", "pptx", "pptx"),
                                           (excel, "xls:MS Excel 97", "xlsx", "xlsx")):
        old = convert(source, legacy, directory / ("legacy-" + modern), skill)
        new = convert(old, modern, directory / ("converted-" + modern), skill)
        if modern == "docx":
            assert "Alpha" in run(["pandoc", "-t", "markdown", new])
        elif modern == "pptx":
            assert "Overview" in run([str(Path(sys.executable).parent / "markitdown"), new])
        else:
            converted = load_workbook(new, read_only=True)
            assert converted["汇总"]["A1"].value == 2
            converted.close()
    invalid = directory / "invalid.pdf"
    invalid.write_bytes(b"not a PDF")
    try:
        PdfReader(invalid)
    except Exception:
        pass
    else:
        raise AssertionError("invalid PDF unexpectedly parsed")
    assert all(hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in before.items())
    print(json.dumps({"status": "passed", "fixtures": str(directory), "originals_unchanged": True,
                      "checks": ["docx-chinese-table", "xlsx-formulas-cache-missing", "pptx-order-notes", "pdf-pages-table", "chinese-ocr", "office-render", "doc-ppt-xls-conversion", "invalid-pdf"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
