import pymupdf
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
p=Path('informe/latex/reporte_eva02.pdf');d=pymupdf.open(p);out=Path('tmp/pdf_revision');out.mkdir(parents=True,exist_ok=True)
thumbs=[]
for i,page in enumerate(d):
 pix=page.get_pixmap(matrix=pymupdf.Matrix(.65,.65),alpha=False);im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.save(out/f'pagina_{i+1:02}.png')
 canvas=Image.new('RGB',(420,565),'#dedede');im.thumbnail((400,530));canvas.paste(im,((420-im.width)//2,25));ImageDraw.Draw(canvas).text((12,6),f'Pagina {i+1}',fill='black');thumbs.append(canvas)
cols=3;rows=(len(thumbs)+cols-1)//cols;contact=Image.new('RGB',(cols*420,rows*565),'white')
for i,im in enumerate(thumbs):contact.paste(im,((i%cols)*420,(i//cols)*565))
contact.save(out/'contacto.png');print('Paginas:',len(d));print('Longitud texto:',sum(len(p.get_text()) for p in d))
