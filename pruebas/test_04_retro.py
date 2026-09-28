# -*- coding: utf-8 -*-
"""Pruebas 04 · nota desglosada y retroalimentación descargable."""
from playwright.sync_api import sync_playwright
from base import URL, T, llenar, JS_STUB
import pathlib, tempfile

with sync_playwright() as pw:
    b = pw.chromium.launch()
    t = T()
    ctx = b.new_context(viewport={'width': 1000, 'height': 1300}, accept_downloads=True)
    pg = ctx.new_page()
    pg.goto(URL); pg.wait_for_timeout(400)

    # todo bien menos un ítem de subnetting de 1 pt → 99
    llenar(pg, True)
    idx1 = pg.evaluate("() => SUBNET.findIndex(s => s.pts === 1)")
    pg.evaluate("""(i) => {
      const el = document.querySelector(`input[data-subnet="${i}"]`);
      el.value = ''; el.dispatchEvent(new Event('input', {bubbles:true}));
    }""", idx1)
    pg.evaluate(JS_STUB)
    pg.click('#btnRevisar'); pg.wait_for_timeout(400)

    zona = pg.inner_text('#zonaResultado')
    Z = zona.upper()   # las tarjetas usan CSS uppercase
    t.ok('99 / 100 pts' in zona, f'encabezado con 99/100 ({zona.splitlines()[1][:40] if len(zona.splitlines())>1 else zona[:40]})')
    t.ok('PARTE II · SUBNETTING' in Z and '9 / 10' in zona, 'tarjeta Parte II con 9/10')
    t.ok('PARTE I · TEORÍA' in Z and '50 / 50' in zona, 'tarjeta Parte I con 50/50')
    t.ok('PARTE III · PRÁCTICOS' in Z and '40 / 40' in zona, 'tarjeta Parte III con 40/40')
    t.ok('99%' in zona and 'Nota 99' in zona, 'porcentaje y nota en escala 0–100')

    with pg.expect_download() as dl:
        pg.click('#btnRetro')
    arch = dl.value
    t.ok(arch.suggested_filename == 'retroalimentacion-E00001.html',
         f'nombre del archivo: {arch.suggested_filename}')
    ruta = pathlib.Path(tempfile.gettempdir()) / 'retro_test.html'
    arch.save_as(str(ruta))
    h = ruta.read_text(encoding='utf-8')

    t.ok('Retroalimentación generada automáticamente' in h, 'pie del documento')
    t.ok('E00001' in h, 'carné del estudiante en el documento')
    t.ok('Parte I · Teoría — 39 buenas de 39' in h, 'Parte I: 39 buenas de 39')
    t.ok('Parte II · Subnetting — 6 de 7 ítems' in h, 'Parte II: 6 de 7 ítems')
    t.ok('Parte III · Prácticos — 12 de 12 incisos' in h, 'Parte III: 12 de 12 incisos')
    t.ok('Sin responder' in h, 'marca lo que no se respondió')
    t.ok('Respuesta correcta:' in h, 'Parte II explica la respuesta correcta en la incorrecta')
    t.ok(h.count('Correcto') >= 12, f'lista los correctos ({h.count("Correcto")})')
    t.ok('https://' not in h.replace('https://riaigtmuixwzgwvjmugx', ''), 'no filtra claves de Supabase al documento')
    ruta.unlink()

    # todo mal → la retroalimentación explica las 39
    pg.reload(); pg.wait_for_timeout(400)
    llenar(pg, False)
    pg.evaluate(JS_STUB)
    pg.click('#btnRevisar'); pg.wait_for_timeout(400)
    t.ok('0 / 100 pts' in pg.inner_text('#zonaResultado'), 'todo mal da 0/100')
    with pg.expect_download() as dl2:
        pg.click('#btnRetro')
    ruta2 = pathlib.Path(tempfile.gettempdir()) / 'retro_test2.html'
    dl2.value.save_as(str(ruta2))
    h2 = ruta2.read_text(encoding='utf-8')
    t.ok('Parte I · Teoría — 0 buenas de 39' in h2, 'Parte I: 0 buenas de 39')
    t.ok(h2.count('Respuesta correcta:') >= 46,
         f'explica teoría y subnetting incorrectos ({h2.count("Respuesta correcta:")} veces)')
    t.ok(h2.count('Lo que se esperaba') >= 12,
         f'explica los 12 incisos de prácticos ({h2.count("Lo que se esperaba")} veces)')
    t.ok(h2.count('Por qué:') >= 39, f'explica las 39 de teoría ({h2.count("Por qué:")} veces)')
    t.ok('¡Excelente! No tiene preguntas incorrectas' in h, 'Parte I sin errores dice que no hay incorrectas')
    t.ok('Parte II · Subnetting — 0 de 7 ítems' in h2, 'Parte II: 0 de 7')
    t.ok('Parte III · Prácticos — 0 de 12 incisos' in h2, 'Parte III: 0 de 12')
    ruta2.unlink()

    ctx.close(); b.close()
    t.fin('04_retro')
