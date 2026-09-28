# -*- coding: utf-8 -*-
"""Pruebas 01 · el examen completo: carga, render, calificación y guardado."""
from playwright.sync_api import sync_playwright
from base import URL, ADMIN, T, abrir, llenar, JS_STUB

with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={'width': 1000, 'height': 1300})
    t = T()
    errs = []
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(500)

    # --- render ---
    counts = pg.evaluate("""() => ({
      teoria: document.querySelectorAll('#examenTeoria [name^=t], [data-theory]').length,
      radios: document.querySelectorAll('input[type=radio][name^=t]').length,
      subnet: document.querySelectorAll('input[data-subnet]').length,
      textareas: document.querySelectorAll('textarea[data-caso]').length,
      casos: PRACTICOS.length,
      svg: document.querySelectorAll('svg').length,
      divisionOculta: getComputedStyle(document.getElementById('panelDivision')).display === 'none'
    })""")
    t.ok(counts['subnet'] == 7, f"7 ítems de subnetting ({counts['subnet']})")
    t.ok(counts['textareas'] == 12, f"12 incisos de prácticos ({counts['textareas']})")
    t.ok(counts['casos'] == 3, f"3 casos prácticos ({counts['casos']})")
    t.ok(counts['svg'] >= 3, f"SVG de topologías presentes ({counts['svg']})")
    t.ok(counts['divisionOculta'], 'el panel de división arranca oculto')

    # --- todo correcto = 100 ---
    llenar(pg, True)
    r = pg.evaluate("() => ({ i: calcularPI(), ii: calcularPII(), iii: calcularPIII() })")
    t.ok(r['i'] == {'pts': 50, 'total': 50}, f"teoría todo correcto: {r['i']}")
    t.ok(r['ii'] == {'pts': 10, 'total': 10}, f"subnetting todo correcto: {r['ii']}")
    t.ok(r['iii'] == {'pts': 40, 'total': 40}, f"prácticos todo correcto: {r['iii']}")
    t.ok(r['i']['pts'] + r['ii']['pts'] + r['iii']['pts'] == 100, 'total 100/100')

    # --- todo incorrecto = 0 ---
    llenar(pg, False)
    r = pg.evaluate("() => ({ i: calcularPI(), ii: calcularPII(), iii: calcularPIII() })")
    t.ok(r['i']['pts'] == 0 and r['ii']['pts'] == 0 and r['iii']['pts'] == 0,
         f"todo incorrecto da 0 en las tres partes: {r}")
    t.ok(all(x['total'] > 0 for x in r.values()), 'los totales por parte no se pierden')

    # --- guardar sin nombre ---
    pg.evaluate("() => { document.getElementById('nombre').value=''; document.getElementById('carnet').value=''; }")
    pg.evaluate(JS_STUB)
    llenar(pg, True)
    pg.evaluate("() => { document.getElementById('nombre').value=''; document.getElementById('carnet').value=''; }")
    pg.click('#btnRevisar'); pg.wait_for_timeout(300)
    t.ok('nombre y carné' in pg.inner_text('#zonaEstado'), 'pide nombre y carné')
    t.ok(pg.evaluate("() => window.__inserts.length") == 0, 'no inserta sin nombre/carné')

    # --- guardar completo ---
    pg.evaluate("() => { document.getElementById('nombre').value='Estudiante Prueba'; document.getElementById('carnet').value='E00001'; }")
    pg.click('#btnRevisar'); pg.wait_for_timeout(400)
    ins = pg.evaluate("() => window.__inserts")
    t.ok(len(ins) == 1, f"un solo intento insertado ({len(ins)})")
    t.ok(ins and ins[0]['pts_total'] == 100, f"payload con 100 pts ({ins[0]['pts_total']})")
    t.ok('respuestas' in ins[0] and len(ins[0]['respuestas']['teoria']) == 39,
         'payload incluye las 39 respuestas de teoría')
    t.ok('Intento guardado' in pg.inner_text('#zonaEstado'), 'mensaje de éxito')
    t.ok(pg.is_visible('#btnRetro'), 'aparece el botón de retroalimentación')
    t.ok(not errs, f'sin errores JS en el examen: {errs[:2]}')

    # --- admin ---
    adm_errs = []
    adm = ctx.new_page()
    adm.on('pageerror', lambda e: adm_errs.append(str(e)))

    def stub(route):
        route.fulfill(
            body="export function createClient(){return {auth:{getSession:async()=>({data:{session:null}}),"
                 "signInWithPassword:async()=>({data:{user:{email:'p@ucr.ac.cr'}},error:null}),"
                 "signOut:async()=>({})},from:()=>({select:()=>({order:async()=>({data:[],error:null})})})};}",
            content_type='application/javascript')
    adm.route('**/esm.sh/**', stub)
    adm.goto(ADMIN); adm.wait_for_timeout(500)
    t.ok(adm.is_visible('#formLogin'), 'admin muestra el login')
    t.ok(adm.is_visible('#btnExportar') is False, 'admin oculta los reportes hasta entrar')
    t.ok(not adm_errs, f'admin sin errores JS: {adm_errs[:2]}')

    ctx.close(); b.close()
    t.fin('01_index')
