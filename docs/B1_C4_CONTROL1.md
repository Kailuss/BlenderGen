# B1-C4 — primer control causal, 2026-10-26

Estado: avance validado; B1-C4 y B1.0 NO cerrados.

## Separación de líneas

Base limpia de este trabajo: e19a52b, rama codex/b1-c4-causal.
La línea anterior de física/render queda conservada por separado en
codex/physics-render-wip-20261025, commit dd71ba7. No se integra en C4.

## Implementado

- RemovalLedger con inventario, secuencia, causas, CUT y REMOVE; serialización
  validada y persistencia en metadatos/caché. Operaciones confirmadas de derrumbe,
  poda, agujeros y recortes arquitectónicos posteriores a la entrada en assembly.
- Replay causal independiente de la malla final. REMOVE propaga pérdida; CUT
  produce incertidumbre salvo prueba de que la caja de corte no alcanza la cota
  del contacto horizontal. Este último atajo solo vale para piezas raíz.
- Regla de asiento geométrico compartida: dos de tres rayos, offsets X
  -1.5/0/1.5 mm y Z -2.7 mm. Incluye mortero como la regla heredada. No certifica
  longitud de entrega, área resistente ni capacidad mecánica.
- Informe de correspondencia viga/eje/segmento por ambos extremos, con estado
  explícito UNMAPPED si no hay coincidencia única. En este ensayo no hay escaleras.
- Funciones comunes de IDs de piezas, segmentos y vigas. Los IDs de piezas aún
  dependen del nombre completo dentro de la generación; NO certifican estabilidad
  semántica entre regeneraciones. Los ordinales de eje se conservan antes del filtro.

## Evidencias

`python dev.py test`: 51 pruebas puras y cuatro casos geométricos con digests
idénticos a expected; cierre de mallas y sesión/caché incluidos en el probe.
`tests/blender_b1_c4_causal.py`: tres semillas (1,20,73), dos cotas de forjado;
38 asientos candidatos por semilla. Datos íntegros: reports/b1_c4_t1.json.
El control negativo retira físicamente todas las piezas de un asiento y exige
pérdida de segmento y viga en el grafo, además de ausencia del contacto por rayos.
Si se omiten esos eventos, la predicción anterior discrepa: control de evento perdido.
No se ha ejecutado Bullet en este control. No hay cambio de geometría pretendido.

## Límites y siguiente control obligatorio

1. El inventario comienza DESPUÉS de construir la fábrica. Las omisiones causadas
   por daño en layout/front_courses todavía no están en el ledger. No es T1 completo.
2. Los contactos iniciales se miden ANTES de las operaciones, no se deducen aún
   íntegramente del layout. La geometría final solo audita, nunca alimenta el replay.
3. Falta cerrar identidad semántica de piezas antes de filtrado y ligar el plan
   directamente al consumidor de vigas; el mapa actual informa, no gobierna.
4. Falta auditar terminaciones en cabecero con escaleras y la migración completa
   de vanos; después corresponde el esqueleto de dos vigas con cabecero.
5. Materiales, capacidades y calibración BALANCED/PRECISE no se alteran.

No se presenta este control como entrega final de B1-C4 ni como estabilidad física.
