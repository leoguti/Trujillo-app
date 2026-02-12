# Reporte: Códigos de Paraderos Duplicados

**Para:** Gerencia de Transporte Metropolitano de Trujillo
**De:** [Tu nombre]
**Fecha:** 2026-02-12
**Asunto:** 11 códigos de paraderos que aparecen duplicados en los datos KML proporcionados

---

## Resumen

Al procesar los datos de paraderos proporcionados por la Gerencia (archivo KMZ con 1,858 registros), se encontraron **11 códigos que están asignados a dos paraderos distintos** ubicados en diferentes puntos de la ciudad. Esto impide identificar unívocamente cada paradero.

Se solicita que se asignen códigos únicos a cada paradero para poder completar la carga de datos al sistema de información geográfica.

---

## Detalle de los Duplicados

### Grupo 1: Códigos PE (9 casos)

Estos 9 códigos aparecen en dos capas distintas del archivo KML ("Consolidado" y "Puntos_Paraderos") y corresponden a paraderos ubicados a **más de 4 km de distancia entre sí**. Son claramente paraderos diferentes que recibieron el mismo código.

| Codigo | Paradero A (lat, lon) | Capa A | Paradero B (lat, lon) | Capa B | Distancia |
|--------|----------------------|--------|----------------------|--------|-----------|
| PE-237 | -8.0496012, -79.0563403 | Consolidado | -8.1065488, -79.0214104 | Puntos_Paraderos | 7,408 m |
| PE-238 | -8.0656021, -79.0449278 | Consolidado | -8.1062447, -79.0213554 | Puntos_Paraderos | 5,211 m |
| PE-239 | -8.0667633, -79.0452012 | Consolidado | -8.1047149, -79.0194718 | Puntos_Paraderos | 5,083 m |
| PE-240 | -8.0684283, -79.0448327 | Consolidado | -8.1042749, -79.0193401 | Puntos_Paraderos | 4,875 m |
| PE-241 | -8.1029616, -79.0176466 | Puntos_Paraderos | -8.0679315, -79.0475825 | Consolidado | 5,102 m |
| PE-242 | -8.0705267, -79.0433503 | Consolidado | -8.1023748, -79.0173110 | Puntos_Paraderos | 4,556 m |
| PE-243 | -8.0719115, -79.0416660 | Consolidado | -8.1009813, -79.0155783 | Puntos_Paraderos | 4,324 m |
| PE-244 | -8.0737571, -79.0412500 | Consolidado | -8.1005072, -79.0153155 | Puntos_Paraderos | 4,123 m |
| PE-247 | -8.0971849, -79.0117809 | Puntos_Paraderos | -8.0821358, -79.0492040 | Consolidado | 4,447 m |

### Grupo 2: Código PL-53

Dos paraderos en la zona de Laredo, a 288 metros de distancia, con el mismo código.

| Codigo | Paradero A (lat, lon) | Paradero B (lat, lon) | Distancia |
|--------|----------------------|----------------------|-----------|
| PL-53  | -8.0849631, -78.9555310 | -8.0823828, -78.9553352 | 288 m |

Ambos aparecen en la capa "LAREDO".

### Grupo 3: Código "PL-Existente"

Dos paraderos en Laredo, a 32 metros de distancia, marcados como "PL-Existente" en vez de tener un código asignado.

| Codigo | Paradero A (lat, lon) | Paradero B (lat, lon) | Distancia |
|--------|----------------------|----------------------|-----------|
| PL-Existente | -8.0924662, -78.9672482 | -8.0927534, -78.9672582 | 32 m |

**Consulta adicional:** El nombre "PL-Existente" no parece ser un código de paradero sino una nota. Se solicita confirmar:
- Si estos dos puntos son paraderos reales que necesitan código
- O si deben descartarse

---

## Mapa de Referencia

Las coordenadas indicadas arriba pueden pegarse directamente en Google Maps para verificar la ubicación de cada paradero.

Formato para copiar: `-8.0496012, -79.0563403`

---

## Acción Solicitada

1. **Para los 9 pares PE-***: Asignar un código nuevo a uno de los dos paraderos de cada par (el otro puede conservar el código actual).
2. **Para PL-53**: Asignar un código diferente a uno de los dos paraderos.
3. **Para PL-Existente**: Confirmar si son paraderos válidos y, de serlo, asignar códigos.

Quedamos atentos a su respuesta para completar la actualización de datos.
