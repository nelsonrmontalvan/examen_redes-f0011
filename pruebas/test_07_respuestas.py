# -*- coding: utf-8 -*-
"""Pruebas 07 · respuestas crudas: guardado en Supabase y lectura en admin.html."""
from playwright.sync_api import sync_playwright
from base import URL, ADMIN, T, llenar, JS_STUB
import json

FAKE_ROWS = [
    {"id": 2, "created_at": "2026-09-28T15:00:00+00:00", "nombre": "Ana Prueba", "carnet": "B01234",
     "grupo": "G1", "pts_teoria": 48, "pts_subnet": 9, "pts_practicos": 36, "pts_total": 93,
     "respuestas": {
       "teoria": [
         {"n": 3, "ok": False, "pregunta": "Pregunta <b>mala</b>", "su": "C · opcion mala",
          "esperada": "B · opcion buena", "just": "Porque sí."},
         {"n": 5, "ok": True, "pregunta": "Pregunta bien", "su": "A · correcta",
          "esperada": "A · correcta", "just": "Justificación."}],
       "subnet": [
         {"n": 1, "ok": True, "pregunta": "¿Cuántos bits?", "su": "2", "esperada": "2"},
         {"n": 2, "ok": False, "pregunta": "Nueva máscara", "su": "/25", "esperada": "/26"}],
       "practicos": [
         {"caso": "Caso 1 · RIP (RIP v2)",
          "items": [
            {"ok": True, "pts": 3, "ptsTotal": 3, "pregunta": "Active RIP v2",
             "su": "conf t, router rip, version 2", "esperada": "conf t, router rip, version 2"},
            {"ok": False, "pts": 0, "ptsTotal": 4, "pregunta": "Redes en R1",
             "su": "network 192.168.1.0",
             "esperada": "network 192.168.1.0, network 10.0.0.0 0.0.0.3"}]}]}},
    {"id": 1, "created_at": "2026-09-27T10:00:00+00:00", "nombre": "Ana Prueba", "carnet": "B01234",
     "grupo": "G1", "pts_teoria": 50, "pts_subnet": 10, "pts_practicos": 40, "pts_total": 100,
     "respuestas": None},
]

with sync_playwright() as pw:
    b = pw.chromium.launch()
    t = T()

    # ---------- index.html: payload ----------
    ctx = b.new_context(viewport={'width': 1000, 'height': 1300})
    pg = ctx.new_page()
    pg.goto(URL); pg.wait_for_timeout(400)

    res = pg.evaluate("""() => {
      TEORIA.forEach((p,i)=>{
        if (p.tipo==='mc'){ const el = document.querySelector(`input[name="t${i}"][value="${p.resp}"]`); if (el) el.click(); }
        else { const el = document.querySelector(`input[data-theory="${i}"]`); if (el) el.value = p.resp; }
      });
      SUBNET.forEach((s,i)=>{ const el = document.querySelector(`input[data-subnet="${i}"]`); if (el) el.value = s.respuesta; });
      const idxMalo = SUBNET.findIndex(x => x.pts === 1);                    // ítem de 1 pt sin responder
      document.querySelector(`input[data-subnet="${idxMalo}"]`).value = '';
      PRACTICOS.forEach((c,ci)=> c.items.forEach((it,ii)=>{
        const ta = document.querySelector(`textarea[data-caso="${ci}"][data-item="${ii}"]`);
        if (ta) ta.value = it.r;
      }));
      document.querySelector('textarea[data-caso="0"][data-item="0"]').value = '';  // sin responder (3 pts)
      document.getElementById('nombre').value = 'Ana Prueba';
      document.getElementById('carnet').value = 'B01234';
      return { t: TEORIA.length, s: SUBNET.length, p: PRACTICOS.reduce((a,c)=>a+c.items.length,0),
               p0: PRACTICOS[0].items[0].pts, sub1: SUBNET.find(x=>x.pts===1) ? 1 : 0 };
    }""")
    esperado = 100 - res['sub1'] - res['p0']
    t.ok(res['t'] == 40 and res['s'] == 7 and res['p'] == 12,
         f"encuesta: {res['t']} teoría, {res['s']} subnet, {res['p']} incisos")

    pg.evaluate(JS_STUB)
    pg.click('#btnRevisar'); pg.wait_for_timeout(400)

    payload = pg.evaluate("() => window.__inserts[0]")
    t.ok(payload is not None, 'se intentó insertar el intento')
    t.ok(payload['pts_total'] == esperado, f"pts_total = {payload.get('pts_total')} (esperado {esperado})")

    r = payload.get('respuestas')
    t.ok(isinstance(r, dict), 'payload incluye respuestas')
    if isinstance(r, dict):
        t.ok(len(r.get('teoria', [])) == 40, f"teoría: {len(r.get('teoria', []))} ítems")
        t.ok(all(x['ok'] for x in r['teoria']), 'las 40 de teoría marcadas ok')
        t.ok(all(x['su'] for x in r['teoria']), 'las 40 tienen su respuesta')
        t.ok(all('esperada' in x and 'pregunta' in x for x in r['teoria']), 'teoría con pregunta y esperada')
        malos = [x for x in r['subnet'] if not x['ok']]
        t.ok(len(malos) == 1 and malos[0]['su'] == '', 'subnet sin responder: ok=false, su vacío')
        t.ok(all(x['su'] == x['esperada'] for x in r['subnet'] if x['ok']), 'subnet contestada tal cual')
        casos = r.get('practicos', [])
        t.ok(len(casos) == 3, f"{len(casos)} casos")
        pitems = [i for c in casos for i in c['items']]
        t.ok(len(pitems) == 12, f"prácticos: {len(pitems)} incisos")
        t.ok(sum(1 for i in pitems if not i['ok']) == 1, 'exactamente 1 inciso sin responder')
        t.ok(all(i['ok'] for i in pitems[1:]), 'los demás marcados ok')
        t.ok(pitems[0]['ok'] is False and pitems[0]['pts'] == 0 and pitems[0]['ptsTotal'] == res['p0'],
             f"inciso sin responder: 0/{res['p0']}")
        t.ok(len(json.dumps(r, ensure_ascii=False)) < 40000, 'tamaño del JSON razonable')
    t.ok('Intento guardado' in pg.inner_text('#zonaEstado'), 'mensaje de guardado correcto')

    # fallback: si falta la columna, guarda solo el puntaje
    pg.evaluate("""() => {
      window.__inserts = [];
      let n = 0;
      getSupabase = async () => ({
        from: () => ({ insert: async (payload) => {
          window.__inserts.push(payload); n++;
          return n === 1 ? { error: { message: 'column "respuestas" of relation "intentos" does not exist' } }
                         : { error: null };
        } })
      });
    }""")
    pg.click('#btnRevisar'); pg.wait_for_timeout(400)
    ins = pg.evaluate("() => window.__inserts")
    t.ok(len(ins) == 2, f"reintento: {len(ins)} inserts")
    t.ok('respuestas' not in ins[-1], 'el reintento va sin la columna')
    t.ok('columna respuestas' in pg.inner_text('#zonaEstado'), 'aviso de migración mostrado')
    ctx.close()

    # ---------- admin.html: lectura ----------
    adm_errs = []
    adm = b.new_page(viewport={'width': 1100, 'height': 1300})
    adm.on('pageerror', lambda e: adm_errs.append(str(e)))

    def stub(route):
        route.fulfill(
            body="export function createClient(){return {auth:{getSession:async()=>({data:{session:null}}),"
                 "signInWithPassword:async()=>({data:{user:{email:'prof@ucr.ac.cr'}},error:null}),"
                 "signOut:async()=>({})},from:()=>({select:()=>({order:async()=>({data:globalThis.__FAKE_ROWS__,error:null})})})};}",
            content_type='application/javascript')

    adm.route('**/esm.sh/**', stub)
    adm.add_init_script("window.__FAKE_ROWS__ = " + json.dumps(FAKE_ROWS))
    adm.goto(ADMIN)
    adm.wait_for_timeout(600)

    h = adm.evaluate("() => window.htmlRespuestas(window.__FAKE_ROWS__[0].respuestas)")
    t.ok('Parte I · incorrectas (1)' in h, 'incorrectas de teoría')
    t.ok('Pregunta &lt;b&gt;mala&lt;/b&gt;' in h, 'escapa HTML del estudiante')
    t.ok('Caso 1 · RIP' in h, 'casos de la Parte III')
    t.ok('conf t, router rip, version 2' in h, 'texto escrito por el estudiante')
    t.ok('Esperada' in h, 'muestra la respuesta esperada en las malas')
    t.ok('/26' in h, 'esperada de subnetting')
    t.ok('no tiene respuestas guardadas' in adm.evaluate("() => window.htmlRespuestas(null)"),
         'aviso para intentos antiguos')

    adm.fill('#loginEmail', 'prof@ucr.ac.cr')
    adm.fill('#loginPass', 'x')
    adm.click('#formLogin button[type=submit]')
    adm.wait_for_timeout(400)
    t.ok(adm.is_visible('#panelDatos'), 'login con sesión simulada')

    adm.click('#tablaResumen tr[data-carnet]')
    adm.wait_for_timeout(300)
    t.ok(adm.is_visible('#detalleEstudiante'), 'detalle del estudiante visible')
    btns = adm.query_selector_all('#tablaDetalle .btnVerResp')
    t.ok(len(btns) == 2, f"{len(btns)} botones Ver (uno por intento)")
    filas = adm.query_selector_all('#tablaDetalle tr[data-resp]')
    t.ok(len(filas) == 2 and all('hidden' in (f.get_attribute('class') or '') for f in filas),
         'las filas de respuestas arrancan ocultas')

    btns[0].click(); adm.wait_for_timeout(200)
    c0 = adm.query_selector('#tablaDetalle tr[data-resp="0"]')
    t.ok('hidden' not in (c0.get_attribute('class') or ''), '1er Ver despliega la fila')
    t.ok('no tiene respuestas guardadas' in c0.inner_text(), 'aviso en intentos antiguos')

    btns[1].click(); adm.wait_for_timeout(200)
    c1 = adm.query_selector('#tablaDetalle tr[data-resp="1"]')
    t.ok('hidden' not in (c1.get_attribute('class') or ''), '2º Ver despliega la fila')
    txt = c1.inner_text()
    t.ok('network 192.168.1.0' in txt, 'lee lo que escribió en prácticos')
    t.ok('incorrectas (1)' in txt, 'incorrectas de teoría')
    t.ok('/25' in txt, 'lee la respuesta equivocada de subnetting')
    t.ok(not adm_errs, f'admin sin errores JS: {adm_errs[:2]}')

    adm.close(); b.close()
    t.fin('07_respuestas')
