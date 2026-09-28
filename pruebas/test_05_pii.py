# -*- coding: utf-8 -*-
"""Pruebas 05 · calificación de la Parte II (subnetting)."""
from playwright.sync_api import sync_playwright
from base import URL, T

VACIAR = """() => {
  SUBNET.forEach((s,i)=>{
    const el = document.querySelector(`input[data-subnet="${i}"]`);
    if (el) el.value = '';
  });
}"""

CONTESTAR = """(i) => {
  const el = document.querySelector(`input[data-subnet="${i}"]`);
  el.value = SUBNET[i].respuesta;
}"""

MAL = """(i) => {
  const el = document.querySelector(`input[data-subnet="${i}"]`);
  el.value = '999.999.999.999';
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch()
    t = T()
    pg = b.new_page()
    pg.goto(URL); pg.wait_for_timeout(400)

    # todo correcto
    pg.evaluate("""() => SUBNET.forEach((s,i)=>{
      document.querySelector(`input[data-subnet="${i}"]`).value = s.respuesta;
    })""")
    t.ok(pg.evaluate("() => calcularPII()") == {'pts': 10, 'total': 10}, 'todo correcto = 10/10')

    # todo mal
    pg.evaluate("""() => SUBNET.forEach((s,i)=>{
      document.querySelector(`input[data-subnet="${i}"]`).value = '999.999.999.999';
    })""")
    t.ok(pg.evaluate("() => calcularPII()")['pts'] == 0, 'todo mal = 0')

    # sin responder nada
    pg.evaluate(VACIAR)
    t.ok(pg.evaluate("() => calcularPII()") == {'pts': 0, 'total': 10}, 'vacío = 0')

    # cada ítem puntúa lo que vale
    parcial = []
    for i in range(7):
        pg.evaluate(VACIAR)
        pg.evaluate(CONTESTAR, i)
        r = pg.evaluate("() => calcularPII()")
        esperado = pg.evaluate("(i) => SUBNET[i].pts", i)
        parcial.append(r['pts'] == esperado and r['total'] == 10)
    t.ok(all(parcial), f'cada ítem aporta sus propios puntos ({sum(parcial)}/7)')

    # tolerancia de formato (mayúsculas, espacios, guiones, barra)
    tolerancia = pg.evaluate("""() => {
      const casos = [];
      SUBNET.forEach((s,i)=>{
        const el = document.querySelector(`input[data-subnet="${i}"]`);
        el.value = '  ' + s.respuesta.toUpperCase() + '  ';
        const conBarra = esCorrectaTexto(s.respuesta, el.value);
        el.value = s.respuesta.replaceAll('/','');           // sin la barra "/26" → "26"
        const sinBarra = esCorrectaTexto(s.respuesta, el.value);
        el.value = s.respuesta.replace(/ a /g, '-');          // rango con guion
        const guion = esCorrectaTexto(s.respuesta, el.value);
        casos.push({ conBarra, sinBarra, guion, resp: s.respuesta });
      });
      return casos;
    }""")
    t.ok(all(c['conBarra'] for c in tolerancia), 'acepta espacios extra y mayúsculas')
    t.ok(all(c['sinBarra'] for c in tolerancia), 'acepta "26" aunque la respuesta sea "/26"')
    t.ok(all(c['guion'] for c in tolerancia), 'acepta "1-62" aunque la respuesta diga "a"')

    # valores incorrectos no pasan
    malos = pg.evaluate("""() => SUBNET.every(s => !esCorrectaTexto(s.respuesta, '999.999.999.999'))""")
    t.ok(malos, 'valores ajenos no cuentan como correctos')
    t.ok(pg.evaluate("() => esCorrectaTexto('172.16.50.0', '')") is False, 'vacío nunca puntúa')

    pg.close(); b.close()
    t.fin('05_pii')
