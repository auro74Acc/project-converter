"""
Interfaz web para conversión de plantillas de proyecto ↔ Asana
Uso: python app.py
Luego abre http://localhost:5000 en tu navegador
"""

import os, sys, tempfile
from flask import Flask, request, send_file, jsonify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convert_to_asana as c2a
import asana_to_project as a2p

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Project Converter</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0e0e10;
    --surface: #17171a;
    --surface2: #1f1f24;
    --border: #2e2e35;
    --accent: #5b8aff;
    --accent2: #ff6b6b;
    --text: #e8e8ec;
    --muted: #6b6b78;
    --success: #4ade80;
    --radius: 12px;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 48px 24px;
  }
  body::before {
    content: '';
    position: fixed; inset: 0;
    background-image:
      linear-gradient(rgba(91,138,255,.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(91,138,255,.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none; z-index: 0;
  }
  .container { width: 100%; max-width: 720px; position: relative; z-index: 1; }
  header { text-align: center; margin-bottom: 48px; }
  header .eyebrow { font-size: 11px; letter-spacing: .2em; text-transform: uppercase; color: var(--accent); margin-bottom: 12px; }
  header h1 { font-family: 'DM Serif Display', serif; font-size: clamp(2rem, 6vw, 3.2rem); line-height: 1.1; color: #fff; }
  header h1 em { font-style: italic; color: var(--accent); }
  header p { margin-top: 16px; color: var(--muted); font-size: 13px; line-height: 1.6; }
  .modes { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 32px; }
  .mode-btn {
    background: var(--surface); border: 1.5px solid var(--border);
    border-radius: var(--radius); padding: 20px; cursor: pointer;
    transition: all .2s; text-align: left; position: relative; overflow: hidden;
  }
  .mode-btn::before { content: ''; position: absolute; inset: 0; background: var(--accent); opacity: 0; transition: opacity .2s; }
  .mode-btn:hover::before { opacity: .05; }
  .mode-btn.active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 8%, var(--surface)); }
  .mode-btn .icon { font-size: 24px; margin-bottom: 10px; display: block; }
  .mode-btn .label { font-size: 12px; font-weight: 500; color: #fff; letter-spacing: .05em; text-transform: uppercase; }
  .mode-btn .desc { font-size: 11px; color: var(--muted); margin-top: 4px; line-height: 1.5; }
  .mode-btn .tag {
    display: inline-block; margin-top: 8px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 4px; padding: 2px 7px; font-size: 10px;
    color: var(--muted); letter-spacing: .05em;
  }
  .mode-btn.active .tag { background: color-mix(in srgb, var(--accent) 15%, transparent); border-color: var(--accent); color: var(--accent); }
  .upload-card { background: var(--surface); border: 1.5px solid var(--border); border-radius: var(--radius); padding: 28px; }
  .drop-zone {
    border: 1.5px dashed var(--border); border-radius: 8px;
    padding: 40px 24px; text-align: center; cursor: pointer;
    transition: all .2s; position: relative;
  }
  .drop-zone:hover, .drop-zone.drag-over { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 5%, transparent); }
  .drop-zone input[type=file] { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; }
  .drop-icon { font-size: 36px; margin-bottom: 12px; display: block; }
  .drop-title { font-size: 14px; color: #fff; margin-bottom: 6px; }
  .drop-sub { font-size: 11px; color: var(--muted); }
  .drop-sub span { color: var(--accent); font-weight: 500; cursor: pointer; }
  .file-info { display: none; align-items: center; gap: 12px; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; margin-top: 16px; }
  .file-info.visible { display: flex; }
  .file-info .file-icon { font-size: 20px; }
  .file-info .file-name { font-size: 12px; color: #fff; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file-info .file-size { font-size: 11px; color: var(--muted); }
  .file-info .remove-btn { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 16px; padding: 2px 4px; transition: color .2s; }
  .file-info .remove-btn:hover { color: var(--accent2); }
  .convert-btn {
    width: 100%; margin-top: 20px; background: var(--accent); color: #fff;
    border: none; border-radius: 8px; padding: 14px 24px;
    font-family: 'DM Mono', monospace; font-size: 13px; font-weight: 500;
    letter-spacing: .08em; text-transform: uppercase; cursor: pointer;
    transition: all .2s;
  }
  .convert-btn:hover { background: color-mix(in srgb, var(--accent) 85%, #fff); transform: translateY(-1px); }
  .convert-btn:active { transform: translateY(0); }
  .convert-btn:disabled { opacity: .4; cursor: not-allowed; transform: none; }
  .status { margin-top: 16px; padding: 12px 16px; border-radius: 8px; font-size: 12px; display: none; align-items: center; gap: 10px; }
  .status.visible { display: flex; }
  .status.loading { background: color-mix(in srgb, var(--accent) 10%, var(--surface2)); border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent); color: var(--accent); }
  .status.success { background: color-mix(in srgb, var(--success) 10%, var(--surface2)); border: 1px solid color-mix(in srgb, var(--success) 30%, transparent); color: var(--success); }
  .status.error { background: color-mix(in srgb, var(--accent2) 10%, var(--surface2)); border: 1px solid color-mix(in srgb, var(--accent2) 30%, transparent); color: var(--accent2); }
  .spinner { width: 14px; height: 14px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin .7s linear infinite; flex-shrink: 0; }
  @keyframes spin { to { transform: rotate(360deg); } }
  footer { margin-top: 48px; text-align: center; font-size: 11px; color: var(--muted); letter-spacing: .05em; }
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="eyebrow">Project Management Tools</div>
    <h1>Project<br><em>Converter</em></h1>
    <p>Convierte entre la plantilla de proyecto Excel<br>y el formato de importación de Asana.</p>
  </header>
  <div class="modes">
    <button class="mode-btn active" id="btn-excel" onclick="setMode('excel')">
      <span class="icon">📊</span>
      <div class="label">Excel → Asana</div>
      <div class="desc">Exporta la plantilla de proyecto al formato CSV de Asana.</div>
      <span class="tag">.xlsx → .csv</span>
    </button>
    <button class="mode-btn" id="btn-asana" onclick="setMode('asana')">
      <span class="icon">🔄</span>
      <div class="label">Asana → Excel</div>
      <div class="desc">Importa un CSV de Asana a la plantilla de proyecto Excel.</div>
      <span class="tag">.csv → .xlsx</span>
    </button>
  </div>
  <div class="upload-card">
    <div class="drop-zone" id="drop-zone">
      <input type="file" id="file-input" accept=".xlsx">
      <span class="drop-icon">📁</span>
      <div class="drop-title">Arrastra el fichero aquí</div>
      <div class="drop-sub">o <span onclick="document.getElementById('file-input').click()">selecciónalo</span> desde tu equipo</div>
    </div>
    <div class="file-info" id="file-info">
      <span class="file-icon" id="file-icon">📄</span>
      <span class="file-name" id="file-name">—</span>
      <span class="file-size" id="file-size">—</span>
      <button class="remove-btn" onclick="clearFile()" title="Eliminar">✕</button>
    </div>
    <button class="convert-btn" id="convert-btn" disabled onclick="doConvert()">
      Convertir y descargar
    </button>
    <div class="status" id="status">
      <span id="status-icon"></span>
      <span id="status-msg"></span>
    </div>
  </div>
  <footer>Project Converter · Los archivos se procesan localmente y no se almacenan.</footer>
</div>
<script>
let mode = 'excel', selectedFile = null;
function setMode(m) {
  mode = m;
  document.getElementById('btn-excel').classList.toggle('active', m==='excel');
  document.getElementById('btn-asana').classList.toggle('active', m==='asana');
  document.getElementById('file-input').accept = m==='excel' ? '.xlsx' : '.csv';
  clearFile(); hideStatus();
}
function clearFile() {
  selectedFile = null;
  document.getElementById('file-info').classList.remove('visible');
  document.getElementById('file-input').value = '';
  document.getElementById('convert-btn').disabled = true;
}
function hideStatus() { document.getElementById('status').className = 'status'; }
function showStatus(type, msg) {
  const s = document.getElementById('status');
  s.className = 'status visible ' + type;
  document.getElementById('status-icon').innerHTML = type==='loading' ? '<span class="spinner"></span>' : type==='success' ? '✓' : '✕';
  document.getElementById('status-msg').textContent = msg;
}
function formatSize(b) {
  return b < 1024 ? b+' B' : b < 1048576 ? (b/1024).toFixed(1)+' KB' : (b/1048576).toFixed(1)+' MB';
}
function onFileSelected(file) {
  if (!file) return;
  const ext = file.name.split('.').pop().toLowerCase();
  const expected = mode==='excel' ? 'xlsx' : 'csv';
  if (ext !== expected) { showStatus('error', `Formato incorrecto. Se espera un fichero .${expected}.`); return; }
  hideStatus();
  selectedFile = file;
  document.getElementById('file-icon').textContent = ext==='xlsx' ? '📊' : '📋';
  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-size').textContent = formatSize(file.size);
  document.getElementById('file-info').classList.add('visible');
  document.getElementById('convert-btn').disabled = false;
}
document.getElementById('file-input').addEventListener('change', e => onFileSelected(e.target.files[0]));
const dz = document.getElementById('drop-zone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('drag-over'); onFileSelected(e.dataTransfer.files[0]); });
async function doConvert() {
  if (!selectedFile) return;
  const btn = document.getElementById('convert-btn');
  btn.disabled = true;
  showStatus('loading', 'Convirtiendo...');
  const fd = new FormData();
  fd.append('file', selectedFile);
  fd.append('mode', mode);
  try {
    const res = await fetch('/convert', { method: 'POST', body: fd });
    if (!res.ok) { const err = await res.json(); showStatus('error', err.error || 'Error desconocido.'); btn.disabled = false; return; }
    const blob = await res.blob();
    const cd = res.headers.get('Content-Disposition') || '';
    const nameMatch = cd.match(/filename="?([^"]+)"?/);
    const outName = nameMatch ? nameMatch[1] : (mode==='excel' ? 'output.csv' : 'output.xlsx');
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = outName; a.click();
    URL.revokeObjectURL(url);
    showStatus('success', `"${outName}" descargado correctamente.`);
  } catch(e) { showStatus('error', 'Error de conexión con el servidor.'); }
  btn.disabled = false;
}
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

@app.route("/convert", methods=["POST"])
def convert():
    mode = request.form.get("mode", "excel")
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No se recibió ningún fichero."}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        in_name  = file.filename
        in_path  = os.path.join(tmpdir, in_name)
        file.save(in_path)
        base     = os.path.splitext(in_name)[0]
        try:
            if mode == "excel":
                out_name = base + ".csv"
                out_path = os.path.join(tmpdir, out_name)
                c2a.convert(in_path, out_path)
                mime = "text/csv"
            else:
                out_name = base + ".xlsx"
                out_path = os.path.join(tmpdir, out_name)
                a2p.convert(in_path, out_path)
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            # Read into memory before temp dir is deleted (fixes Windows file lock)
            import io
            with open(out_path, 'rb') as fh:
                data = io.BytesIO(fh.read())
            data.seek(0)
            return send_file(data, mimetype=mime, as_attachment=True, download_name=out_name)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    is_local = port == 5000
    if is_local:
        print("=" * 50)
        print("  Project Converter")
        print("  Abre http://localhost:5000 en tu navegador")
        print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=False)
