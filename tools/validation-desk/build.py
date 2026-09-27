from pathlib import Path

root = Path(__file__).resolve().parent
html = (root / 'index.template.html').read_text()
html = html.replace('/* MODEL */', (root / 'model.js').read_text())
html = html.replace('/* RUNNER */', (root / 'runner.js').read_text())
html = html.replace('/* INTEGRITY */', (root / 'integrity.js').read_text())
html = html.replace('/* FIXTURE */', (root / 'fixtures/historical-report.json').read_text())
(root / 'index.html').write_text(html)
