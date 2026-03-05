# Estado P0 – Secuencial SIN POO (Simulado)

Baseline **secuencial** para el sistema de sincronización de semáforos.  
**Sin clases, sin interfaces, sin patrón Strategy**: solo funciones y un bucle secuencial.

Pipeline por intersección:

`read(i) -> analyze(i) -> optimize(features) -> update(i, plan)`

## Ejecutar

```bash
python run_p0.py --n 50 --cycles 3
```

Parámetros:
- `--n`: número de intersecciones
- `--cycles`: ciclos de control
- `--io-ms`: latencia simulada de lectura (ms)
- `--update-ms`: latencia simulada de actualización (ms)
- `--cpu-work`: carga CPU simulada (iteraciones)
