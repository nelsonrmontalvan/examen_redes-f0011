# -*- coding: utf-8 -*-
"""Utilidades compartidas de las pruebas del examen (Playwright + Chromium)."""
from playwright.sync_api import sync_playwright
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
URL = BASE.joinpath('index.html').as_uri()
ADMIN = BASE.joinpath('admin.html').as_uri()


class T:
    def __init__(self):
        self.fallos = []

    def ok(self, cond, msg):
        print(('PASS ' if cond else 'FAIL ') + msg)
        if not cond:
            self.fallos.append(msg)

    def fin(self, etiqueta=''):
        print()
        if self.fallos:
            print(f'FALLAS ({etiqueta}):', len(self.fallos))
            for f in self.fallos:
                print(' -', f)
            raise SystemExit(1)
        print('TODO OK', etiqueta)


JS_LLENAR = """(correctas) => {
  TEORIA.forEach((p,i)=>{
    if (p.tipo==='mc'){
      const oi = correctas ? p.resp : (p.resp+1) % p.opciones.length;
      const el = document.querySelector(`input[name="t${i}"][value="${oi}"]`);
      if (el) el.click();
    } else {
      const el = document.querySelector(`input[data-theory="${i}"]`);
      if (el) el.value = correctas ? p.resp : 'esta respuesta esta mal';
    }
  });
  SUBNET.forEach((s,i)=>{
    const el = document.querySelector(`input[data-subnet="${i}"]`);
    if (el) el.value = correctas ? s.respuesta : 'valor equivocado';
  });
  PRACTICOS.forEach((c,ci)=> c.items.forEach((it,ii)=>{
    const ta = document.querySelector(`textarea[data-caso="${ci}"][data-item="${ii}"]`);
    if (ta) ta.value = correctas ? it.r : 'esto esta mal';
  }));
  document.getElementById('nombre').value = 'Estudiante Prueba';
  document.getElementById('carnet').value = 'E00001';
  document.getElementById('grupo').value = 'G1';
  return true;
}"""

JS_STUB = """() => {
  window.__inserts = [];
  getSupabase = async () => ({
    from: () => ({ insert: async (p) => { window.__inserts.push(p); return { error: null }; } })
  });
}"""


def abrir(pg=None, ctx=None):
    """Abre el examen y espera a que esté listo."""
    pg = pg or ctx.new_page()
    pg.goto(URL)
    pg.wait_for_timeout(400)
    return pg


def llenar(pg, correctas=True):
    pg.evaluate(JS_LLENAR, correctas)
    return pg


def errores_js(pg):
    lista = []
    pg.on('pageerror', lambda e: lista.append(str(e)))
    return lista
