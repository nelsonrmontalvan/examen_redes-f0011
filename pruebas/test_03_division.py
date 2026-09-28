# -*- coding: utf-8 -*-
"""Pruebas 03 · Parte II: clave 1977, bloqueo al 3er fallo, PIN 0101 y geometría del SVG."""
from playwright.sync_api import sync_playwright
from base import URL, T

JS_GEOMETRIA = """() => {
  const svg = document.getElementById('svgGuia2');
  const sr = svg.getBoundingClientRect();
  const fuera = [];
  svg.querySelectorAll('rect, text, line').forEach(el=>{
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return;
    if (r.left < sr.left - 2 || r.top < sr.top - 2 || r.right > sr.right + 2 || r.bottom > sr.bottom + 2)
      fuera.push((el.textContent || el.id || el.tagName).slice(0, 30));
  });
  const cajas = [...svg.querySelectorAll('rect')].filter(el=>{
    const r = el.getBoundingClientRect();
    return r.width > 40 && r.height > 20 && r.width < 600;  // excluye el fondo del SVG
  }).map(el=>el.getBoundingClientRect());
  let solapes = 0;
  for (let i=0;i<cajas.length;i++) for (let j=i+1;j<cajas.length;j++){
    const a=cajas[i], b=cajas[j];
    if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) solapes++;
  }
  return { fuera, solapes, cajas: cajas.length,
           vb: svg.getAttribute('viewBox'),
           divVisible: getComputedStyle(document.getElementById('panelDivision')).display !== 'none',
           ipsVisible: getComputedStyle(document.getElementById('ipsRespuestas')).display !== 'none' };
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch()
    t = T()

    # ---------- contexto nuevo: 3 fallos y bloqueo ----------
    ctx = b.new_context(viewport={'width': 1000, 'height': 1300})
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(400)

    g0 = pg.evaluate(JS_GEOMETRIA)
    t.ok(not g0['divVisible'], 'la división arranca oculta')
    t.ok(not g0['ipsVisible'], 'las IPs de respuesta arrancan ocultas')
    t.ok('Sede Central' in pg.evaluate("() => document.getElementById('svgGuia2').textContent"),
         'la topología base sí es visible')
    t.ok(g0['fuera'] == [], f"SVG sin elementos fuera del lienzo (estado oculto): {g0['fuera'][:4]}")
    t.ok(g0['solapes'] == 0, f"SVG sin cajas solapadas (estado oculto): {g0['solapes']} solapes")
    t.ok(g0['cajas'] >= 8, f"hay cajas de PCs/routers dibujadas ({g0['cajas']})")

    t.ok(not pg.is_disabled('#btnPedirDivision'), 'el botón de clave arranca habilitado')
    pg.click('#btnPedirDivision')
    t.ok(pg.is_visible('#formDivision'), 'el formulario de clave se abre')

    for n in (1, 2, 3):
        pg.fill('#inputDivision', '0000')
        pg.click('#btnOKDivision'); pg.wait_for_timeout(120)
        msg = pg.inner_text('#msgDivision')
        if n < 3:
            t.ok(f'Intento {n} de 3' in msg, f'fallo {n}: avisa "Intento {n} de 3"')
        else:
            t.ok('bloqueada tras 3 intentos' in msg, f'fallo 3: bloquea ({msg})')

    t.ok(pg.is_disabled('#btnPedirDivision'), 'tras el 3er fallo el botón queda deshabilitado')
    t.ok(not pg.is_visible('#formDivision'), 'el formulario queda cerrado')
    t.ok(pg.evaluate("() => localStorage.getItem('examenDivisionBloqueada')") == '1', 'el bloqueo se persiste')
    pg.reload(); pg.wait_for_timeout(400)
    t.ok(pg.is_disabled('#btnPedirDivision'), 'el bloqueo sobrevive a la recarga')

    # PIN del docente: revela y desbloquea
    pg.click('#btnProfesor')
    pg.fill('#pinInput', '0101')
    pg.click('#btnPinOk'); pg.wait_for_timeout(300)
    g1 = pg.evaluate(JS_GEOMETRIA)
    t.ok(g1['divVisible'], 'el PIN 0101 revela la división')
    t.ok(g1['ipsVisible'], 'el PIN 0101 revela las IPs de respuesta')
    t.ok('172.16.50.64/26' in pg.evaluate("() => document.getElementById('ipsRespuestas').textContent"),
         'las IPs aparecen en pantalla')
    t.ok(g1['vb'] == '0 0 800 470', f"el viewBox crece a 470 ({g1['vb']})")
    t.ok(not pg.is_disabled('#btnPedirDivision'), 'el PIN desbloquea el botón')
    t.ok(g1['fuera'] == [], f"SVG sin desbordes tras revelar: {g1['fuera'][:4]}")
    t.ok(g1['solapes'] == 0, f"SVG sin solapes tras revelar: {g1['solapes']}")
    t.ok(pg.evaluate("() => localStorage.getItem('examenDivisionBloqueada')") is None,
         'revelar limpia el bloqueo guardado')
    ctx.close()

    # ---------- contexto nuevo: clave correcta 1977 ----------
    ctx = b.new_context(viewport={'width': 1000, 'height': 1300})
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(400)
    pg.click('#btnPedirDivision')
    pg.fill('#inputDivision', '1977')
    pg.click('#btnOKDivision'); pg.wait_for_timeout(300)
    g2 = pg.evaluate(JS_GEOMETRIA)
    t.ok(g2['divVisible'], 'la clave 1977 revela la división')
    t.ok(g2['ipsVisible'], 'la clave 1977 revela las IPs')
    t.ok('División de bloques visible' in pg.inner_text('#msgDivision'), 'mensaje de éxito')
    t.ok(pg.is_hidden('#btnPedirDivision'), 'el botón se oculta al revelar')
    t.ok(g2['fuera'] == [] and g2['solapes'] == 0, 'SVG válido también con la clave correcta')
    ctx.close()

    # ---------- PIN del docente: bloqueo al 3er intento fallido ----------
    ctx = b.new_context(viewport={'width': 1000, 'height': 1300})
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(400)
    t.ok(not pg.is_visible('#clave'), 'las respuestas arrancan ocultas')
    pg.click('#btnProfesor')
    for n in (1, 2, 3):
        pg.fill('#pinInput', '9999')
        pg.click('#btnPinOk'); pg.wait_for_timeout(120)
        msg = pg.inner_text('#pinError')
        if n < 3:
            t.ok(f'Intento {n} de 3' in msg, f'PIN fallo {n}: avisa "Intento {n} de 3"')
        else:
            t.ok('bloqueado tras 3' in msg, f'PIN fallo 3: bloquea ({msg})')
    t.ok(pg.is_disabled('#pinInput'), 'tras el 3er fallo el campo queda deshabilitado')
    t.ok(pg.is_disabled('#btnPinOk'), 'tras el 3er fallo el botón queda deshabilitado')
    t.ok(pg.evaluate("() => localStorage.getItem('examenPinBloqueada')") == '1', 'el bloqueo del PIN se persiste')
    t.ok(not pg.is_visible('#clave'), 'el PIN bloqueado no revela nada')

    # ni con el PIN correcto se pasa (seguimos bloqueados)
    pg.evaluate("""() => {
      document.getElementById('pinInput').disabled = false;
      document.getElementById('pinInput').value = '0101';
      document.getElementById('pinInput').disabled = true;
      document.getElementById('btnPinOk').dispatchEvent(new Event('click'));
    }""")
    t.ok(not pg.is_visible('#clave'), 'con el PIN bloqueado ni el 0101 revela')

    pg.reload(); pg.wait_for_timeout(400)
    pg.click('#btnProfesor')
    t.ok(pg.is_disabled('#pinInput'), 'el bloqueo del PIN sobrevive a la recarga')
    t.ok('bloqueado' in pg.inner_text('#pinError'), 'al abrir el modal avisa que está bloqueado')

    # una recarga con localStorage limpio: el 0101 sigue funcionando
    pg.evaluate("() => { localStorage.removeItem('examenPinBloqueada'); localStorage.removeItem('examenIntentosPin'); }")
    pg.reload(); pg.wait_for_timeout(400)
    pg.click('#btnProfesor')
    pg.fill('#pinInput', '0101')
    pg.click('#btnPinOk'); pg.wait_for_timeout(300)
    t.ok(pg.is_visible('#clave'), 'el 0101 revela las respuestas cuando no está bloqueado')
    t.ok(not pg.is_disabled('#pinInput') and not pg.is_disabled('#btnPinOk'),
         'los controles quedan habilitados tras un acierto')
    t.ok(pg.evaluate("() => localStorage.getItem('examenPinBloqueada')") is None,
         'un acierto limpia el bloqueo guardado')
    ctx.close()

    # ---------- la clave no se imprime ----------
    ctx = b.new_context()
    pg = ctx.new_page(); pg.goto(URL); pg.wait_for_timeout(300)
    t.ok(pg.evaluate("() => getComputedStyle(document.getElementById('btnPedirDivision')).display !== 'none'"),
         'los controles de clave existen en pantalla')
    t.ok(pg.evaluate("""() => {
      const el = document.getElementById('btnPedirDivision');
      return el.closest('.no-print') !== null;
    }"""), 'los controles de clave están marcados no-print (no salen en el PDF)')
    ctx.close()
    b.close()

    t.fin('03_division')
