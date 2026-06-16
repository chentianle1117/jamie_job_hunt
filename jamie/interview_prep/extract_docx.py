import sys, zipfile, re, os, glob
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def text_from_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml')
    root = ET.fromstring(xml)
    out = []
    body = root.find(f'{NS}body')
    if body is None:
        return ''
    def walk(elem):
        # paragraphs
        for child in elem:
            tag = child.tag
            if tag == f'{NS}p':
                para = ''.join(t.text or '' for t in child.iter(f'{NS}t'))
                out.append(para)
            elif tag == f'{NS}tbl':
                for row in child.iter(f'{NS}tr'):
                    cells = []
                    for cell in row.findall(f'{NS}tc'):
                        ctext = ''.join(t.text or '' for t in cell.iter(f'{NS}t'))
                        cells.append(ctext.strip())
                    out.append(' | '.join(cells))
            else:
                walk(child)
    walk(body)
    return '\n'.join(line for line in out)

os.makedirs('extracted', exist_ok=True)
for f in sorted(glob.glob('intake/*.docx')):
    try:
        txt = text_from_docx(f)
        base = os.path.splitext(os.path.basename(f))[0]
        with open(f'extracted/{base}.txt', 'w') as fh:
            fh.write(txt)
        print(f'{len(txt):>7} chars  {base}')
    except Exception as e:
        print(f'  ERROR  {f}: {e}')
