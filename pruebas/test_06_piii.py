# -*- coding: utf-8 -*-
"""Pruebas 06 · calificación de la Parte III (casos prácticos)."""
from playwright.sync_api import sync_playwright
from base import URL, T

VACIAR = """() => document.querySelectorAll('textarea[data-caso]').forEach(t => t.value = '')"""

CONTESTAR_CASO = """(ci) => {
  PRACTICOS[ci].items.forEach((it,ii)=>{
    document.querySelector(`textarea[data-caso="${ci}"][data-item="${ii}"]`).value = it.r;
  });
}"""

MAL_CASO = """(ci) => {
  PRACTICOS[ci].items.forEach((it,ii)=>{
    document.querySelector(`textarea[data-caso="${ci}"][data-item="${ii}"]`).value = 'comando incorrecto';
  });
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch()
    t = T()
    pg = b.new_page()
    pg.goto(URL); pg.wait_for_timeout(400)

    pg.evaluate("""() => PRACTICOS.forEach((c,ci)=> c.items.forEach((it,ii)=>{
      document.querySelector(`textarea[data-caso="${ci}"][data-item="${ii}"]`).value = it.r;
    }))""")
    r = pg.evaluate("() => calcularPIII()")
    t.ok(r == {'pts': 40, 'total': 40}, f'todo correcto = 40/40 ({r})')

    pg.evaluate("""() => PRACTICOS.forEach((c,ci)=> c.items.forEach((it,ii)=>{
      document.querySelector(`textarea[data-caso="${ci}"][data-item="${ii}"]`).value = 'comando incorrecto';
    }))""")
    r = pg.evaluate("() => calcularPIII()")
    t.ok(r['pts'] == 0 and r['total'] == 40, f'todo mal = 0/40 ({r})')

    pg.evaluate(VACIAR)
    t.ok(pg.evaluate("() => calcularPIII()") == {'pts': 0, 'total': 40}, 'sin responder = 0')

    parciales = []
    for ci in range(3):
        pg.evaluate(VACIAR)
        pg.evaluate(CONTESTAR_CASO, ci)
        r = pg.evaluate("() => calcularPIII()")
        esperado = pg.evaluate("(ci) => PRACTICOS[ci].pts", ci)
        parciales.append(r['pts'] == esperado and r['total'] == 40)
    t.ok(all(parciales), f'cada caso aporta sus 13/13/14 puntos ({sum(parciales)}/3)')

    # inciso por inciso: solo uno correcto aporta sus pts
    inc = []
    for ci in range(3):
        for ii in range(pg.evaluate("(ci) => PRACTICOS[ci].items.length", ci)):
            pg.evaluate(VACIAR)
            pg.evaluate("""([ci,ii]) => {
              const it = PRACTICOS[ci].items[ii];
              document.querySelector(`textarea[data-caso="${ci}"][data-item="${ii}"]`).value = it.r;
            }""", [ci, ii])
            r = pg.evaluate("() => calcularPIII()")
            esperado = pg.evaluate("([ci,ii]) => PRACTICOS[ci].items[ii].pts", [ci, ii])
            inc.append(r['pts'] == esperado)
    t.ok(all(inc), f'cada inciso aporta sus propios puntos ({sum(inc)}/{len(inc)})')

    # tolerancia de formato: mayúsculas, espacios y comas opcionales
    tol = pg.evaluate("""() => {
      const res = [];
      PRACTICOS.forEach((c,ci)=> c.items.forEach((it,ii)=>{
        const el = document.querySelector(`textarea[data-caso="${ci}"][data-item="${ii}"]`);
        el.value = '   ' + it.r.toUpperCase().replace(/,/g, ' ,  ') + '   ';
        res.push(esCorrectaTexto(it.r, el.value));
        if (!it.r.includes('|')){
          el.value = it.r.split(',').slice(0,-1).join(',');   // le quita el último fragmento
          if (el.value !== it.r) res.push(!esCorrectaTexto(it.r, el.value));
        }
      }));
      return res;
    }""")
    t.ok(all(tol), f'acepta mayúsculas/espacios y rechaza respuestas incompletas ({sum(tol)}/{len(tol)})')

    # una respuesta vacía nunca puntúa
    pg.evaluate(VACIAR)
    t.ok(pg.evaluate("() => PRACTICOS.every(c => c.items.every(it => !esCorrectaTexto(it.r, '')))"),
         'respuesta vacía nunca es correcta')

    pg.close(); b.close()
    t.fin('06_piii')
