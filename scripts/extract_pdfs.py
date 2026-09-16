from pdfminer.high_level import extract_text

for i in range(1, 5):
    path = fr'C:\Users\HP\Desktop\iia_project\class_notes\iia-{i}.pdf'
    try:
        text = extract_text(path)
        out_path = fr'C:\Users\HP\Desktop\iia_project\class_notes\iia-{i}.txt'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'iia-{i}.pdf -> {len(text)} chars written')
    except Exception as e:
        print(f'Error reading iia-{i}: {e}')
