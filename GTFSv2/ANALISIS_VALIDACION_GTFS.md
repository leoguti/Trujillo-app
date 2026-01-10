# 📋 Análisis del Reporte de Validación GTFS

**Fecha de validación:** 2026-01-09  
**Validador:** MobilityData v7.1.0  
**Feed validado:** gtfs_trujillo.zip

---

## ✅ RESUMEN GENERAL

### Archivos procesados correctamente:
- ✅ agency.txt (37 agencias)
- ✅ calendar.txt
- ✅ routes.txt (79 rutas)
- ✅ shapes.txt (210 shapes)
- ✅ stop_times.txt (11,133 registros)
- ✅ stops.txt (2,180 paradas)
- ✅ trips.txt (210 trips)

### Contadores:
- **Agencias:** 37
- **Rutas:** 79
- **Trips:** 210
- **Paradas:** 2,180
- **Shapes:** 210

---

## ❌ ERRORES CRÍTICOS (6 total)

### `duplicate_key` - Claves duplicadas en routes.txt

**Problema:** Algunas rutas tienen route_id duplicado

**Afectados:**
1. M-28 A (filas 22 y 55)
2. C-13 D (filas 44 y 69)
3. C-39 S (filas 42 y 74)
4. C-15 P1 (filas 78 y 84)
5. C-33 P2 (filas 81 y 85)
6. C-45 C (filas 45 y 86)

**Impacto:** ERROR - Feed inválido  
**Solución:** Eliminar duplicados o renombrar con sufijos (_1, _2, etc.)

---

## ⚠️ ADVERTENCIAS (40 total)

### 1. `fast_travel_between_consecutive_stops` (20 avisos)

**Problema:** Velocidades irreales entre paradas consecutivas (400-700+ km/h)

**Ejemplos:**
- Trip 19972496 (C-32 S): **713 km/h** - 35.7 km en 2 minutos
- Trip 19972461 (C-30 C): **659 km/h** - 32.9 km en 2 minutos
- Trip 19988606 (C-15 P1): **410 km/h** - 20.5 km en 2 minutos

**Causa:** Los tiempos estimados (2 minutos fijos entre paradas) no son realistas para:
- Paradas sintéticas muy alejadas del comienzo/fin de ruta
- Rutas largas con pocas paradas

**Impacto:** WARNING - Feed válido pero poco realista  
**Solución:** 
- Calcular tiempos basados en distancia real
- Usar velocidad promedio de 20-30 km/h para buses urbanos
- Ajustar tiempos para las paradas sintéticas

### 2. `fast_travel_between_far_stops` (20 avisos)

**Problema:** Similar al anterior, detecta velocidades altas entre paradas lejanas

**Mismos casos que el punto 1**

---

## 📊 ANÁLISIS DETALLADO

### Problema 1: Route IDs Duplicados

**¿Por qué ocurre?**
- El archivo `routes.txt` original tiene 6 rutas con IDs repetidos
- Probablemente son variantes de la misma ruta (ej: ida/vuelta)

**¿Cómo solucionarlo?**

```bash
# Opción 1: Verificar routes.txt original
grep "M-28 A\|C-13 D\|C-39 S\|C-15 P1\|C-33 P2\|C-45 C" routes.txt

# Opción 2: Crear script para renombrar duplicados
# M-28 A → M-28 A-1, M-28 A-2
```

### Problema 2: Tiempos Irreales

**Situación actual:**
```python
# Código en generate_gtfs_files.py (línea 64)
time_minutes = start_time_minutes + (stop_seq - 1) * 2
# Intervalo fijo: 2 minutos entre TODAS las paradas
```

**Problema:**
- Parada sintética al inicio puede estar a 30+ km de la primera parada real
- Con 2 minutos = 900+ km/h de velocidad

**Solución sugerida:**
```python
# Calcular tiempo basado en distancia
def calculate_travel_time(distance_km, avg_speed_kmh=25):
    """
    distance_km: distancia entre paradas
    avg_speed_kmh: velocidad promedio (20-30 km/h urbano)
    """
    time_hours = distance_km / avg_speed_kmh
    time_minutes = int(time_hours * 60)
    return max(time_minutes, 1)  # Mínimo 1 minuto
```

---

## 🔧 RECOMENDACIONES

### Prioridad ALTA (Errores)

1. **Corregir route_id duplicados en routes.txt**
   ```bash
   # Identificar duplicados
   cd gtfs_feed
   cut -d',' -f1 routes.txt | sort | uniq -d
   
   # Renombrar manualmente o con script
   ```

### Prioridad MEDIA (Warnings importantes)

2. **Ajustar tiempos de viaje**
   - Calcular basado en distancia real entre paradas
   - Usar velocidad promedio de 25 km/h para transporte urbano
   - Las paradas sintéticas necesitan tiempos especiales

3. **Revisar ubicación de paradas sintéticas**
   - Algunas están a 20-35 km de la siguiente parada
   - Considerar no crear sintéticas si están muy lejos
   - O ajustar el umbral de 10m a un valor mayor

### Prioridad BAJA (Mejoras)

4. **Agregar información adicional**
   - feed_info.txt con información del publisher
   - Horarios reales de servicio (actualmente todos empiezan a 06:00)

---

## 📈 MÉTRICAS DE CALIDAD

| Métrica | Estado | Detalle |
|---------|--------|---------|
| Archivos requeridos | ✅ 100% | Todos presentes |
| Errores críticos | ❌ 6 | route_id duplicados |
| Warnings velocidad | ⚠️ 40 | Tiempos irreales |
| Estructura GTFS | ✅ Válida | Formato correcto |
| Paradas únicas | ✅ 2,180 | Todas con stop_id |
| Trips procesados | ✅ 210 | 100% completos |

---

## 🚀 PASOS SIGUIENTES

1. **Inmediato:** Corregir duplicados en routes.txt
2. **Corto plazo:** Implementar cálculo de tiempos por distancia
3. **Mediano plazo:** Validar y ajustar paradas sintéticas
4. **Largo plazo:** Agregar horarios reales de servicio

---

**Estado del feed:** ⚠️ FUNCIONAL CON ADVERTENCIAS  
**Validación completa:** https://gtfs-validator-results.mobilitydata.org/758ca941-ca15-4540-80b1-5b3adf261908/report.json

