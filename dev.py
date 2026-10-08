"""Herramientas locales sin dependencias externas: comprobar, localizar, probar y empaquetar."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'src'/'ruinas_panel'
EXPECTED=ROOT/'reports'/'expected.json'


def symbols():
    """IA: calcula el índice desde AST; no mantengas manualmente números de línea."""
    result=[]
    for file in sorted(SOURCE.rglob('*.py')):
        tree=ast.parse(file.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                result.append({'name':node.name,'file':str(file.relative_to(ROOT)),
                               'line':node.lineno,'doc':ast.get_docstring(node) or ''})
    return result


def check():
    """IA: comprobación estática rápida; no presenta sintaxis válida como validación de Blender."""
    files=list(SOURCE.rglob('*.py'))+list((ROOT/'tools').glob('*.py'))+list((ROOT/'tests').glob('*.py'))+[Path(__file__)]
    functions=0
    for file in files:
        tree=ast.parse(file.read_text(encoding='utf-8'),filename=str(file))
        compile(tree,str(file),'exec')
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                assert 'IA:' in (ast.get_docstring(node) or ''),(file,node.name,'falta contrato IA')
                functions+=1
            if isinstance(node,ast.ImportFrom):assert all(a.name!='*' for a in node.names),(file,'import *')
    print('CHECK_PASSED',len(files),'archivos',functions,'funciones documentadas')
    import unittest
    if str(ROOT/'src') not in sys.path:sys.path.insert(0,str(ROOT/'src'))
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise RuntimeError('Fallan pruebas de cálculo puro')
    skill=(ROOT/'agent/ruinas-dev/SKILL.md').read_text(encoding='utf-8')
    assert skill.startswith('---\n') and '\n---\n' in skill[4:]
    front=skill.split('---',2)[1]
    fields=dict(line.split(': ',1) for line in front.strip().splitlines())
    assert fields['name']=='ruinas-dev' and len(fields['description'])<1024
    assert set(fields)=={'name','description'}
    assert 'TODO' not in skill and 'TBD' not in skill


def blender_path(explicit):
    """IA: permite Blender explícito; no cambies configuración global para encontrarlo."""
    choices=[explicit,shutil.which('blender'),r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe']
    for choice in choices:
        if choice and Path(choice).is_file():return str(choice)
    raise FileNotFoundError('Indica --blender con la ruta de blender.exe')


def probe(blender, output, legacy=None, case=None):
    """IA: conserva log completo y exige marcador además de exit code; Blender puede ocultar errores Python."""
    cmd=[blender,'-b','-t','4','--python-exit-code','1','--python',str(ROOT/'tests/blender_probe.py'),'--','--output',str(output)]
    if legacy:cmd+=['--legacy',str(Path(legacy).resolve())]
    if case:cmd+=['--case',case]
    output.parent.mkdir(parents=True,exist_ok=True)
    log=output.with_suffix('.log')
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT)
    text=log.read_text(encoding='utf-8')
    if result.returncode or 'PROBE_PASSED' not in text:raise RuntimeError('Prueba fallida: '+str(log))
    print('BLENDER_PASSED',output)
    return json.loads(output.read_text(encoding='utf-8'))


def expected(actual,update=False):
    """IA: compara digests y caras degeneradas con reports/expected.json; solo --update-expected acepta cambios de geometría."""
    version=actual[0]['blender']
    current={r['case']:{'digest':r['digest'],'faces':r['metrics']['faces'],
                        'degenerate_faces':sorted(r['closure']['degenerate_faces'])} for r in actual}
    stored=json.loads(EXPECTED.read_text(encoding='utf-8')) if EXPECTED.is_file() else None
    if update:
        if not stored or stored['blender']!=version:stored={'blender':version,'cases':{}}
        stored['cases'].update(current)
        EXPECTED.write_text(json.dumps(stored,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print('EXPECTED_UPDATED',', '.join(current))
        return
    if not stored:raise RuntimeError('No existe reports/expected.json: créalo con test --update-expected')
    if stored['blender']!=version:
        print('EXPECTED_SKIPPED referencia de Blender',stored['blender'],'y ejecución con',version)
        return
    errors=[]
    for case,now in current.items():
        ref=stored['cases'].get(case)
        if not ref:
            errors.append(f'{case}: sin referencia; usa --update-expected')
            continue
        if now['digest']!=ref['digest']:errors.append(f"{case}: geometría distinta ({ref['faces']} → {now['faces']} caras)")
        new=sorted(set(now['degenerate_faces'])-set(ref['degenerate_faces']))
        if new:errors.append(f'{case}: caras degeneradas nuevas en {new[:5]}')
    if errors:raise RuntimeError('Cambios frente a reports/expected.json:\n  '+'\n  '.join(errors))
    print('EXPECTED_PASSED',', '.join(current))


def calibrate(blender, output):
    """IA: genera en Blender la placa de prueba para resina (STL + leyenda .md); exige marcador además de exit code."""
    output=Path(output).resolve()
    cmd=[blender,'-b','--factory-startup','--python-exit-code','1','--python',str(ROOT/'tools/print_test.py'),'--','--output',str(output)]
    log=output.with_suffix('.log')
    output.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w',encoding='utf-8') as stream:
        result=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode or 'PLATE_READY' not in log.read_text(encoding='utf-8'):raise RuntimeError('Placa fallida: '+str(log))
    print('PLATE_READY',output)
    print('LEYENDA',output.with_suffix('.md'))


def pack(project=False):
    """IA: empaqueta únicamente fuentes del addon; excluye cachés, renders y pruebas del ZIP instalable."""
    check()
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    target=out/'ruinas_panel_v0326.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(SOURCE.rglob('*.py')):archive.write(file,file.relative_to(SOURCE.parent))
    with zipfile.ZipFile(target) as archive:assert archive.testzip() is None
    print('PACKAGED',target)
    if project:
        bundle=out/'ruinas_desarrollo_v0326.zip'
        files=[ROOT/'README.md',ROOT/'AGENTS.md',ROOT/'dev.py',ROOT/'.gitignore',target]
        for folder in ('src','tools','tests','docs','agent'):
            files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
        files.extend(p for p in (ROOT/'reports').glob('*.json') if p.stem in ('baseline','modular','lifecycle','validation','expected'))
        with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(files):archive.write(file,Path('ruinas')/file.relative_to(ROOT))
        with zipfile.ZipFile(bundle) as archive:assert archive.testzip() is None
        print('PROJECT_PACKAGED',bundle)


def main():
    """IA: mantiene comandos pequeños y rutas relativas al proyecto, independientes del cwd."""
    sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('check')
    package=sub.add_parser('pack');package.add_argument('--project',action='store_true')
    locate=sub.add_parser('find');locate.add_argument('query')
    plate=sub.add_parser('calibrate');plate.add_argument('--blender');plate.add_argument('--output',default=str(ROOT/'dist'/'placa_prueba_resina.stl'))
    test=sub.add_parser('test');test.add_argument('--blender');test.add_argument('--baseline',type=Path)
    test.add_argument('--case',choices=['basic_draft','door_windows_work','room_beams_draft','window_detail'])
    test.add_argument('--update-expected',action='store_true',help='acepta la geometría actual como referencia')
    args=parser.parse_args()
    if args.command=='check':check()
    elif args.command=='pack':pack(args.project)
    elif args.command=='calibrate':calibrate(blender_path(args.blender),args.output)
    elif args.command=='find':
        for line in (ROOT/'docs/ARCHITECTURE.md').read_text(encoding='utf-8').splitlines():
            columns=line.split('|')
            if len(columns)>3 and args.query.casefold() in columns[1].casefold():
                print('MÓDULO',columns[2].strip(),'—',columns[1].strip())
        for item in symbols():
            if args.query.casefold() in (item['name']+' '+item['file']+' '+item['doc']).casefold():
                print(f"{item['file']}:{item['line']} {item['name']} — {item['doc']}")
    elif args.command=='test':
        check();exe=blender_path(args.blender)
        if args.baseline:
            baseline=probe(exe,ROOT/'reports/baseline.json',args.baseline,args.case)
        actual=probe(exe,ROOT/'reports/modular.json',case=args.case)
        if args.baseline:
            assert [(r['case'],r['digest']) for r in baseline]==[(r['case'],r['digest']) for r in actual],'La geometría cambió frente a baseline'
            print('PARITY_PASSED')
        expected(actual,args.update_expected)


if __name__=='__main__':main()
