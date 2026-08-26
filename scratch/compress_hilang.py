import json, gzip, base64

with open('data_hilang_keluarga.js', 'r', encoding='utf-8') as f:
    text = f.read()

# the text is `window.dataHilangKeluarga = [...]`
# let's extract the JSON part
json_str = text.split('=', 1)[1].strip().rstrip(';')

data = json.loads(json_str)

# drop all nulls or unused columns
for row in data:
    for k in list(row.keys()):
        if row[k] is None or (isinstance(row[k], float) and str(row[k]) == 'nan'):
            del row[k]
        elif k == 'link_fasih':
            # link fasih is long, just keep the id part
            row[k] = row[k].split('/')[-1]

minified = json.dumps(data, separators=(',', ':'))

# let's check size
print("Minified size:", len(minified) / (1024*1024), "MB")

with open('data_hilang_keluarga.js', 'w', encoding='utf-8') as f:
    f.write('window.dataHilangKeluarga = ')
    f.write(minified)
    f.write(';')
