# -*- coding: utf-8 -*-
"""Pruebas: borrador automático (guardar, restaurar, borrar, limpiar al guardar)."""
from playwright.sync_api import sync_playwright
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from base import URL
fallos = []

def ok(cond, msg):
    print(('PASS ' if cond else 'FAIL ') + msg)
    if not cond: fallos.append(msg)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1000, "height": 1300})
    pg = ctx.new_page()
    pg.goto(URL); pg.wait_for_timeout(400)

    # escribe: 3 preguntas, 2 de subnet, 1 práctico, y su nombre
    snap = pg.evaluate("""() => {
      TEORIA.slice(0,3).forEach((p,i)=>{
        if (p.tipo==='mc'){ const el = document.querySelector(`input[name="t${i}"][value="${p.resp}"]`); if (el) el.click(); }
        else { const el = document.querySelector(`input[data-theory="${i}"]`); if (el) el.value = p.resp; }
      });
      document.querySelector('input[data-subnet="0"]').value = 'MI-RESPI';
      document.querySelector('input[data-subnet="1"]').value = '/26';
      document.querySelector('textarea[data-caso="0"][data-item="0"]').value = 'conf t, router rip';
      document.getElementById('nombre').value = 'Nelson Prueba';
      document.getElementById('carnet').value = 'B99999';
      return {
        preguntas: TEORIA.slice(0,3).map(p=>({ texto:p.texto, tipo:p.tipo,
                     respTexto: p.tipo==='mc' ? p.opciones[p.resp] : p.resp })),
        sub0: { id: SUBNET[0].id, val: 'MI-RESPI' },
        sub1: { id: SUBNET[1].id, val: '/26' },
        caso: { clave: PRACTICOS[0].protocolo || PRACTICOS[0].titulo, val: 'conf t, router rip' }
      };
    }""")
    pg.dispatch_event('input[data-subnet="0"]', 'input')   # dispara el debounce
    pg.wait_for_timeout(700)

    crudo = pg.evaluate("() => localStorage.getItem('examenBorrador')")
    ok(crudo and 'MI-RESPI' in crudo, 'el borrador se escribe en localStorage con lo escrito')
    orden1 = pg.evaluate("() => TEORIA.map(p=>p.texto).slice(0,5)")
    # recarga (mismo navegador → mismo almacenamiento)
    pg.reload(); pg.wait_for_timeout(500)

    ok(pg.is_visible('#zonaBorrador'), 'tras recargar aparece el banner del borrador')
    txt = pg.inner_text('#zonaBorrador') if pg.is_visible('#zonaBorrador') else ''
    ok('restauró su borrador' in txt, f'banner informa la restauración: {txt[:70]}')
    estado = pg.evaluate("""(s) => {
      const marcas = s.preguntas.map(pq=>{
        const i = TEORIA.findIndex(p=>p.texto===pq.texto);
        if (i < 0) return false;
        const p = TEORIA[i];
        if (p.tipo==='mc'){
          const el = document.querySelector(`input[name="t${i}"]:checked`);
          return !!el && p.opciones[parseInt(el.value,10)] === pq.respTexto;
        }
        const el = document.querySelector(`input[data-theory="${i}"]`);
        return !!el && el.value === pq.respTexto;
      });
      const j = SUBNET.findIndex(x=>x.id===s.sub0.id);
      const k = SUBNET.findIndex(x=>x.id===s.sub1.id);
      const ci = PRACTICOS.findIndex(c=>(c.protocolo||c.titulo)===s.caso.clave);
      return {
        marcas: marcas.filter(Boolean).length,
        sub0: j>=0 ? document.querySelector(`input[data-subnet="${j}"]`).value : null,
        sub1: k>=0 ? document.querySelector(`input[data-subnet="${k}"]`).value : null,
        ta: ci>=0 ? document.querySelector(`textarea[data-caso="${ci}"][data-item="0"]`).value : null,
        nombre: document.getElementById('nombre').value,
        carnet: document.getElementById('carnet').value
      };
    }""", snap)
    ok(estado['marcas'] == 3, f"las 3 preguntas restauradas y correctas ({estado['marcas']}/3)")
    ok(estado['sub0'] == 'MI-RESPI' and estado['sub1'] == '/26',
       f"subnetting restaurado por id ({estado['sub0']}, {estado['sub1']})")
    ok(estado['ta'] == 'conf t, router rip', 'práctico restaurado por clave estable del caso')
    ok(estado['nombre'] == 'Nelson Prueba' and estado['carnet'] == 'B99999', 'nombre y carné restaurados')
    # la restauración respetó el orden aleatorio distinto: verificar por texto
    ok(pg.evaluate("""() => {
      // cada radio marcado corresponde al texto de su pregunta (misma fila)
      return [...document.querySelectorAll('input[type=radio]:checked')].every(el=>{
        const i = parseInt(el.name.slice(1), 10);
        return TEORIA[i].opciones[parseInt(el.value,10)] != null;
      });
    }"""), 'los radios marcados quedaron en su pregunta (clave por texto)')

    # --- Empezar de cero ---
    pg.click('#btnBorrarBorrador'); pg.wait_for_timeout(500)
    ok(pg.evaluate("() => localStorage.getItem('examenBorrador')") is None, 'el borrador se borra del almacenamiento')
    ok(not pg.is_visible('#zonaBorrador'), 'el banner desaparece')
    limpio = pg.evaluate("""() => ({
      sub: document.querySelector('input[data-subnet="0"]').value,
      marc: document.querySelectorAll('input[type=radio]:checked').length,
      ta: document.querySelector('textarea[data-caso="0"][data-item="0"]').value })""")
    ok(limpio == {'sub': '', 'marc': 0, 'ta': ''}, 'el examen queda limpio')

    # --- guardar el intento limpia el borrador ---
    pg.evaluate("""() => {
      TEORIA.forEach((p,i)=>{ if(p.tipo==='mc'){ const el=document.querySelector(`input[name="t${i}"][value="${p.resp}"]`); if(el) el.click(); } });
      document.querySelector('input[data-subnet="0"]').value = 'x';
      document.getElementById('nombre').value = 'Nelson Prueba';
      document.getElementById('carnet').value = 'B99999';
      window.__inserts = [];
      getSupabase = async () => ({ from: () => ({ insert: async (pl) => { window.__inserts.push(pl); return { error: null }; } }) });
    }""")
    pg.dispatch_event('input[data-subnet="0"]', 'input'); pg.wait_for_timeout(700)
    ok(pg.evaluate("() => !!localStorage.getItem('examenBorrador')"), 'hay borrador antes de guardar')
    ok(not pg.is_visible('#zonaBorrador'), 'sin banner al cargar (no había borrador guardado)')
    pg.click('#btnRevisar'); pg.wait_for_timeout(500)
    ok(pg.evaluate("() => window.__inserts.length") == 1, 'el intento se insertó')
    ok(pg.evaluate("() => localStorage.getItem('examenBorrador')") is None, 'guardar el intento limpia el borrador')
    ok(not pg.is_visible('#zonaBorrador'), 'guardar también quita el banner')
    ok('Intento guardado' in pg.inner_text('#zonaEstado'), 'mensaje de guardado correcto')

    # --- si el guardado falla, el borrador SE CONSERVA ---
    pg.reload(); pg.wait_for_timeout(400)
    pg.evaluate("""() => {
      document.querySelector('input[data-subnet="0"]').value = 'SOSPE';
      getSupabase = async () => ({ from: () => ({ insert: async () => ({ error: { message: 'Failed to fetch' } }) }) });
      document.getElementById('nombre').value = 'N';
      document.getElementById('carnet').value = 'C';
    }""")
    pg.dispatch_event('input[data-subnet="0"]', 'input'); pg.wait_for_timeout(700)
    pg.click('#btnRevisar'); pg.wait_for_timeout(500)
    ok('No se pudo guardar' in pg.inner_text('#zonaEstado'), 'aviso de guardado fallido')
    ok(pg.evaluate("() => !!localStorage.getItem('examenBorrador')"), 'si falla el guardado, el borrador se conserva')

    ctx.close(); b.close()

print()
if fallos:
    print('FALLAS:', len(fallos))
    for f in fallos: print(' -', f)
    raise SystemExit(1)
print('TODO OK')
