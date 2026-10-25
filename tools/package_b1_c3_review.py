"""Documento contestado y paquete reproducible para revisión B1-C3."""
import ast,hashlib,json,subprocess,zipfile
from pathlib import Path
from docx import Document

ROOT=Path(__file__).resolve().parents[1]
VERSION='B1-C3_2026-10-25'


def git(*args):
    'IA: Consulta Git sin modificarlo y devuelve UTF-8 para identificar fuente y cambios locales.'
    return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf8')


def build():
    'IA: Contesta R1–R8 en copia del DOCX; conserva orden original, adjunta fuentes solicitadas y declara los límites de T1/T2 y del render.'
    source=Path(r'C:\Users\yhora\Downloads\ORDEN B1-C3 fuente única de fachada y baseline con fábrica dañada.docx')
    baseline=json.loads((ROOT/'reports/b1_joint_baseline.json').read_text(encoding='utf8'))
    reports={m:json.loads((ROOT/f'reports/b1_c3_{m}.json').read_text(encoding='utf8')) for m in ('t1','t2')}
    assert all(len(r['cases'])==3 for r in reports.values())
    assert all('front_seat_failed_ray_audit' in c for r in reports.values() for c in r['cases'])
    code=reports['t1']['code_commit'];folder=ROOT/'dist'/f'{VERSION}_{code[:7]}';folder.mkdir(parents=True,exist_ok=True)
    cold=sum(t['cold_seconds'] for t in baseline['front_courses_cost'])/3
    hot=sum(t['cached_mean_seconds'] for t in baseline['front_courses_cost'])/3
    answers=[
        'Adjuntamos los ocho archivos pedidos en sus rutas src/ruinas_panel y tests. construction_plan es un publicador común, pero NO el productor único: delega en stairs.plan, upper_plan y terrace_plan; siguen los duplicados ya identificados. B1.1 permanece pendiente. config.py es la copia de trabajo validada y contiene cambios previos sin publicar; se adjunta el diff y se identifica esta circunstancia en el manifiesto.',
        'Adjuntamos b1_c3_t1.json y b1_c3_t2.json (tres semillas por fase), baseline intacto, logs, catálogo de pruebas nuevas y digests. La suite suma 46 pruebas; la prueba de propiedades genera 200 DAG. T1/T2 completan la medición pero no la aceptación: graph_state y discrepancy son null al faltar eventos puros por piedra. No son cero discrepancias. B1.0 sigue abierto; T4 no se inicia.',
        'AXIS_MATCH_TOLERANCE = 1,5 mm en config_masonry, conservando el umbral heredado. El eje común es la media: cada extremo se desplaza como máximo 0,75 mm, menos que la semianchura de alojamiento de 2,5 mm. Es una justificación geométrica, no resistencia certificada. Se avisa cuando la separación supera 1,2 mm (80 %). Las tolerancias de regresión 0,05/0,001 mm son independientes.',
        'El esqueleto usa ancho de asiento 4,2 mm más dos márgenes de mundo de 30 mm: a 1:60, intervalo total 5,2 mm alrededor del eje. Banda [2,53,4] mm en el primer forjado, asiento nominal de profundidad 3 mm y mínimo de mundo 120 mm. Segmento nivel 0 numera la banda bajo la viga nivel 1. Sí existe cadena segmento→cimentación→terreno, ahora visible en support_chains. Hay prueba de dos bandas: retirar la inferior tumba la superior y su viga. Los candidatos reciben ordinal antes de filter_axes; el esqueleto solo selecciona una viga, no todas las juntas candidatas.',
        'No hay claves con IDs individuales completos de retirada. derrumbe_global guarda conteos por pared y sin_apoyo; huecos_generados guarda centros, cajas y conteos removed/border; huecos_solicitados guarda cantidad. prune_support devuelve un conteo pero no publica un registro de piedras. aparejo_escalonado describe fábrica generada, no todos los eventos posteriores. T1 no puede predecir causalmente estas pérdidas sin añadir esa infraestructura; no usamos las mallas supervivientes como entrada del grafo. La restricción de esta orden impide reescribir destruction/holes para resolverlo aquí.',
        'Confirmamos tres valores: seguro si ambas clausuras mantienen, perdido si ambas pierden, revisión si difieren. loss valida todas las políticas incluso fuera de la pérdida. HOSTED_BY no es SUPPORTED_BY: la carpintería alojada requiere una regla explícita de desaparición de anfitrión; perder un segmento no debe borrar automáticamente el vano entero. Hoy esa regla de daño de carpintería sigue pendiente y no la damos por resuelta.',
        f'Memoización incorporada: firma de ajustes efectivos, 16 entradas en runtime, copia defensiva y sin referencias RNA. Media observada en tres semillas: llamada fría {cold*1000:.3f} ms; llamada en caché {hot*1000:.3f} ms (100 repeticiones por semilla). Incluye firma y copia; resultados en front_courses_cost. Cambiar semilla/ajustes invalida la clave. No se extrapola al tiempo completo de generación.',
        'stairs.py no ha cambiado frente al commit A1 2bcd7be: diff vacío, adjunto como stairs_vs_A1.diff junto al archivo actual. No se ha adelantado T4 ni la refactorización B1.1.'
    ]
    doc=Document(source);slots=[p for p in doc.paragraphs if p.text.strip()=='Respuesta del equipo:']
    assert len(slots)==8
    for p,answer in zip(slots,answers):p.text='Respuesta del equipo: '+answer
    doc.add_heading('Estado de la entrega B1 C3',level=1)
    doc.add_paragraph(f'Versión {VERSION}. Código de auditoría {code}. C1 conserva los cuatro digests y las 18 comparaciones intactas. T1/T2 no aceptados; B1.0 no cerrado. Esta copia responde al documento recibido; no sustituye las limitaciones por una declaración de finalización.')
    for mode,report in reports.items():
        for c in report['cases']:
            doc.add_paragraph(f"{mode.upper()}, semilla {c['seed']}: {len(c['segments'])} segmentos/sondas auditados; {c['generated_front_beams']} vigas frontales; {c['front_seat_failed_ray_audit']} no cumplen los dos de tres rayos del asiento frontal. No certifica apoyo trasero, cabeceros ni estabilidad. Grafo causal pendiente.")
    doc.add_paragraph('La sensibilidad 0,06/0,12/0,24 usa longitud proyectada de piedra en una banda bajo el asiento. No equivale al 12 % de área XY de prune_support ni constituye una calibración. Las cajas pueden sobreestimar una piedra recortada; la auditoría de rayos se informa por separado.')
    doc.save(folder/'Orden_B1-C3_respuestas_equipo.docx')
    (folder/'stairs_vs_A1.diff').write_text(git('diff','2bcd7be','--','src/ruinas_panel/structure/stairs.py') or '# Sin cambios frente a 2bcd7be.\n',encoding='utf8')
    (folder/'working_tree.diff').write_text(git('diff','HEAD'),encoding='utf8')
    (folder/'working_tree_status.txt').write_text(git('status','--short'),encoding='utf8')
    tracked=git('ls-files','src/ruinas_panel','tests','dev.py').splitlines()
    paths=[p for p in tracked if p.endswith('.py')]
    paths += ['docs/CONSTRUCTION_CORE.md','docs/ARCHITECTURE.md','docs/CHANGELOG.md','docs/B1_PROGRESS.md',
              'reports/b1_joint_baseline.json','reports/b1_c3_t1.json','reports/b1_c3_t2.json','reports/b1_c3_validation.log','reports/b1_c3_damage.log','reports/modular.log','reports/expected.json','reports/modular.json']
    catalogue=[]
    for rel in paths:
        if not rel.startswith('tests/test_'):continue
        now=ast.parse((ROOT/rel).read_text(encoding='utf8'))
        old=subprocess.run(['git','show','2bcd7be:'+rel],cwd=ROOT,capture_output=True)
        previous={n.name for n in ast.walk(ast.parse(old.stdout.decode('utf8')) ) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')} if old.returncode==0 else set()
        catalogue += [rel+':'+n.name for n in ast.walk(now) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_') and n.name not in previous]
    (folder/'pruebas_nuevas_desde_A1.json').write_text(json.dumps(catalogue,indent=2),encoding='utf8')
    actual=json.loads((ROOT/'reports/modular.json').read_text(encoding='utf8'));expected=json.loads((ROOT/'reports/expected.json').read_text(encoding='utf8'))
    digests=[{'case':c['case'],'before':expected['cases'][c['case']]['digest'],'after':c['digest']} for c in actual]
    assert all(c['before']==c['after'] for c in digests)
    (folder/'digests_C1.json').write_text(json.dumps(digests,indent=2),encoding='utf8')
    (folder/'README.txt').write_text(f'''Entrega de revisión {VERSION}
Código de auditoría: {code}
NO es un paquete instalable ni B1.0 terminado.
C1 y baseline intacto validados. T1/T2 medidos, sin aceptación causal.
El DOCX contiene respuestas R1–R8 y límites. La revisión visual del DOCX
depende del renderizador disponible; consultar docx_render_status.txt.
Incluye copia de trabajo de fuentes y pruebas, con SHA256 por archivo.
Algunos archivos solicitados (config.py, generation y dependencias) pueden
contener trabajo anterior: working_tree.diff registra diferencias con HEAD.
No se ha publicado ese trabajo ajeno dentro de los commits B1-C3.
No contiene archivos .blend ni vídeos. No se ha enviado por correo.
''',encoding='utf8')
    for rel in paths:
        dst=folder/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/rel).read_bytes())
    print(folder)


def archive(folder):
    'IA: Empaqueta archivos existentes con hashes verificables; excluye el ZIP y residuos de caché.'
    folder=Path(folder)
    files=[p for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json']
    manifest={'version':VERSION,'head_commit':git('rev-parse','HEAD').strip(),'files':{str(p.relative_to(folder)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    target=folder.with_suffix('.zip')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(folder))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name,digest in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    print(target)


if __name__=='__main__':
    import sys
    archive(sys.argv[2]) if len(sys.argv)>1 and sys.argv[1]=='zip' else build()
