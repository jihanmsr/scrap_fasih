import re

options = """<option value="all">Semua Kabupaten/Kota</option>
                                <option value="[01] BANGGAI KEPULAUAN">[01] BANGGAI KEPULAUAN</option>
                                <option value="[02] BANGGAI">[02] BANGGAI</option>
                                <option value="[03] MOROWALI">[03] MOROWALI</option>
                                <option value="[04] POSO">[04] POSO</option>
                                <option value="[05] DONGGALA">[05] DONGGALA</option>
                                <option value="[06] TOLI-TOLI">[06] TOLI-TOLI</option>
                                <option value="[07] BUOL">[07] BUOL</option>
                                <option value="[08] PARIGI MOUTONG">[08] PARIGI MOUTONG</option>
                                <option value="[09] TOJO UNA-UNA">[09] TOJO UNA-UNA</option>
                                <option value="[10] SIGI">[10] SIGI</option>
                                <option value="[11] BANGGAI LAUT">[11] BANGGAI LAUT</option>
                                <option value="[12] MOROWALI UTARA">[12] MOROWALI UTARA</option>
                                <option value="[71] PALU">[71] PALU</option>"""

with open('index.html', 'r') as f:
    html = f.read()

html = html.replace('<option value="all">Semua Kabupaten/Kota</option>', options)

with open('index.html', 'w') as f:
    f.write(html)
