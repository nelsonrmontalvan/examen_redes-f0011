# -*- coding: utf-8 -*-
"""Pruebas 02 · orden aleatorio: distinto en cada carga, mismo contenido y misma calificación."""
from playwright.sync_api import sync_playwright
from base import URL, T, llenar

with sync_playwright() as pw:
    b = pw.chromium.launch()
    t = T()
    cargas = []
    for i in range(3):
        ctx = b.new_context(viewport={'width': 1000, 'height': 1300})
        pg = ctx.new_page()
        pg.goto(URL); pg.wait_for_timeout(400)
        estado = pg.evaluate("""() => ({
          preguntas: TEORIA.map(p=>p.texto),
          opciones: TEORIA.map(p=>p.opciones.join('||')),
          subnet: SUBNET.map(s=>s.id),
          casos: PRACTICOS.map(c=>c.protocolo || c.titulo)
        })""")
        # responde todo bien: demuestra que resp sigue apuntando a la opción correcta
        llenar(pg, True)
        r = pg.evaluate("() => calcularPI().pts + calcularPII().pts + calcularPIII().pts")
        estado['pts'] = r
        cargas.append(estado)
        ctx.close()

    t.ok(all(c['pts'] == 100 for c in cargas),
         f"cada carga califica 100/100 con el orden que sea: {[c['pts'] for c in cargas]}")

    sets_ok = all(set(c['preguntas']) == set(cargas[0]['preguntas']) for c in cargas)
    t.ok(sets_ok, 'las 39 preguntas son las mismas en las 3 cargas')
    t.ok(all(set(c['subnet']) == set(cargas[0]['subnet']) for c in cargas), 'los 7 ítems de subnetting son los mismos')
    t.ok(all(set(c['casos']) == set(cargas[0]['casos']) for c in cargas), 'los 3 casos son los mismos')

    orden_distinto = (cargas[0]['preguntas'] != cargas[1]['preguntas']
                      or cargas[1]['preguntas'] != cargas[2]['preguntas'])
    t.ok(orden_distinto, 'el orden de las preguntas cambia entre cargas')

    ops_distintas = cargas[0]['opciones'] != cargas[1]['opciones'] or cargas[1]['opciones'] != cargas[2]['opciones']
    t.ok(ops_distintas, 'el orden de las opciones cambia entre cargas')

    sub_distinto = cargas[0]['subnet'] != cargas[1]['subnet'] or cargas[1]['subnet'] != cargas[2]['subnet']
    t.ok(sub_distinto, 'el orden de subnetting cambia entre cargas')

    casos_distintos = cargas[0]['casos'] != cargas[1]['casos'] or cargas[1]['casos'] != cargas[2]['casos']
    t.ok(casos_distintos, 'el orden de los casos prácticos cambia entre cargas')

    # en cada carga, la opción marcada como respuesta es efectivamente la correcta
    ctx = b.new_context()
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(400)
    bien = pg.evaluate("""() => {
      const malas = [];
      TEORIA.forEach((p,i)=>{
        if (p.tipo==='mc'){
          const el = document.querySelector(`input[name="t${i}"][value="${p.resp}"]`);
          if (!el || el.value !== String(p.resp)) malas.push(i);
        } else if (!p.resp){ malas.push(i); }
      });
      return malas;
    }""")
    t.ok(bien == [], f'cada pregunta apunta a su opción correcta tras el barajado (malas: {bien})')
    ctx.close(); b.close()

    t.fin('02_orden')
