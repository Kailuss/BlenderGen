# Exportación de chimenea y hogar — pendiente

Observación del usuario, 24 de octubre de 2026. No reproducida todavía por una prueba controlada. A petición del usuario no se cambia esta familia durante B1.

- Preparación detenida por «Demasiados fragmentos de revoco/chimenea: aumenta el tamaño de fragmento o reduce la casa». Log mostrado: `C:\Users\yhora\AppData\Local\Temp\ruinas_physics_0_qpwcxe\worker.log`.
- «Corte frágil no cerrado: Piedra · hogar base.002 · fragmento.001 · fragmento.001 (4 aristas, volumen 254.01043382, enlaces [(1, 2.098e-05), (1, 7.24179602), (1, 7.24179602), (1, 9.54e-06)])». Log mostrado: `C:\Users\yhora\AppData\Local\Temp\ruinas_physics_imu8uztg\worker.log`.
- Quitar la chimenea o cambiar la semilla permite preparar algunos casos. Es una mitigación observada, no una corrección ni prueba de causa exclusiva.

Al retomar: comparar el mismo .blend y semilla con/sin chimenea; contar piezas y fragmentos por familia antes/después de cada corte; conservar la pieza exacta que queda abierta. Investigar por separado el presupuesto de fragmentos y el cierre topológico. No aumentar límites ni densidad para ocultar el problema. Evaluar después una chimenea simplificada y apoyos explícitos coherentes con el esquema común.
