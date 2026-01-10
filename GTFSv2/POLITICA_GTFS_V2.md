# Política de Creación GTFS v2 - Trujillo

## Fecha de Creación
2025-12-31

## Objetivo
Generar una versión realista y funcional del feed GTFS para Trujillo utilizando exclusivamente las paradas validadas y los datos disponibles actuales.

---

## 1. PARADAS (stops.txt)

### Fuente de Datos
- **Única fuente:** `paraderos_consolidados.geojson` (1,857 paradas)
- Archivos KMZ consolidados enviados por Oscar
- **No se generarán paradas sintéticas ni automáticas**

### Clasificación de Paradas
- **Validadas (882 paradas):** Trujillo, Víctor Larco, Salaverry, Laredo, Moche
- **Pendientes de validar (975 paradas):** Marcadas para trabajo de campo

### Criterio de Uso
- Se utilizarán **TODAS** las 1,857 paradas en el GTFS v2
- Las paradas pendientes de validar se incluyen con metadata que indica su estado
- Coordenadas y nombres exactos según fuente original

---

## 2. RUTAS (routes.txt, trips.txt, stop_times.txt)

### Asignación de Paradas a Rutas

**CRITERIO IMPORTANTE:**
- **NO se discrimina por ruta:** Todas las 1,857 paradas están disponibles para todas las rutas
- Las paradas originales pueden tener metadata de rutas específicas, pero **se ignorará**
- El sistema es **inclusivo:** cualquier ruta puede usar cualquier parada

### Direccionalidad y Sentido de Circulación

**CONTEXTO TRUJILLO, PERÚ:**
- Las rutas están creadas **por sentido de circulación**
- Algunas rutas operan en **anillos** (circuitos cerrados)
- En Perú, los vehículos se detienen **al lado derecho** de la vía

**REGLA DE ASIGNACIÓN:**
- Para cada shape de ruta, **solo asignar paradas del lado derecho**
- Calcular qué paradas están al lado derecho del sentido de circulación
- Ignorar paradas del lado izquierdo (sentido contrario)

**EJEMPLO:**
```
Ruta A (Sentido Norte-Sur):
  ✅ Asignar paradas al lado derecho (Este) de la vía
  ❌ NO asignar paradas al lado izquierdo (Oeste) de la vía

Ruta B (Sentido Sur-Norte, ruta diferente):
  ✅ Asignar paradas al lado derecho (Oeste) de la vía
  ❌ NO asignar paradas al lado izquierdo (Este) de la vía
```

### Paradas de Inicio y Fin
**PROBLEMA IDENTIFICADO:**
- Las rutas actuales no tienen paradas de inicio/fin explícitas
- Los trazados (shapes) existen pero sin correspondencia con paradas

**ACCIÓN REQUERIDA:**
- **Agregar paradas de inicio y fin a cada ruta**
- Identificar terminales/puntos de partida reales
- Mapear la primera y última parada de cada recorrido
- Generar `stop_times.txt` coherente con paradas reales

### Metodología
1. Analizar shapes de rutas existentes
2. Para cada shape, calcular qué lado es el "lado derecho" del sentido de circulación
3. Identificar paradas cercanas al shape que estén al lado derecho
4. Seleccionar parada de inicio (más cercana al punto inicial del shape)
5. Seleccionar paradas intermedias al lado derecho a lo largo del recorrido
6. Seleccionar parada de fin (más cercana al punto final del shape)
7. Asignar horarios básicos (al menos 2-3 viajes por ruta)

---

## 3. CONFIGURACIÓN PLANIFICADOR (OTP)

### Contexto
- **Cobertura limitada:** 1,857 paradas no cubren toda la ciudad
- **Distancias entre paradas:** Pueden superar los 300-500m en zonas periféricas
- **Necesidad:** Usuarios deben caminar más para acceder al transporte

### Ajustes Requeridos en OTP (Futuro)
> ⚠️ **NOTA:** Estos cambios NO se implementan en esta fase, solo se documentan

**Parámetros a modificar:**
- `maxWalkDistance`: Aumentar de 800m a **1,500-2,000m**
- `walkSpeed`: Mantener en 1.33 m/s (velocidad promedio)
- `walkReluctance`: Reducir de 2.0 a **1.5** (hacer caminata más atractiva)
- `maxPreTransitTime`: Aumentar a 30-40 minutos

**Justificación:**
- Realismo: Refleja la realidad del transporte en Trujillo
- Cobertura: Permite que más usuarios accedan a rutas disponibles
- Gradual: A medida que se agreguen más paradas, se pueden ajustar parámetros

---

## 4. CALIDAD DE DATOS

### Principios
- **Realismo sobre perfección:** Mejor un GTFS funcional que uno teórico
- **Datos reales:** Solo usar información verificable
- **Iterativo:** v2 es base para mejoras futuras (v3, v4...)
- **Transparencia:** Documentar limitaciones conocidas

### Limitaciones Conocidas
1. Cobertura de paradas incompleta en zonas periféricas
2. Horarios aproximados (sin datos de operadores)
3. Frecuencias estimadas basadas en observación
4. Falta validación de campo para 975 paradas

---

## 5. ENTREGABLES GTFS v2

### Archivos Obligatorios
- `agency.txt` - Información de operadores
- `stops.txt` - **1,857 paradas consolidadas**
- `routes.txt` - Rutas con ID, nombre, tipo
- `trips.txt` - Viajes por ruta (mínimo 2-3 por ruta)
- `stop_times.txt` - **Con inicio y fin definidos**
- `calendar.txt` - Días de operación

### Archivos Opcionales
- `shapes.txt` - Trazado geográfico de rutas (si disponible)
- `feed_info.txt` - Metadata del feed

---

## 6. PRÓXIMOS PASOS

### Fase Actual (v2)
1. ✅ Consolidar paradas (COMPLETADO)
2. ⏳ Agregar paradas inicio/fin a rutas
3. ⏳ Generar GTFS v2 funcional
4. ⏳ Validar con GTFS validator

### Futuras Versiones
- **v3:** Trabajo de campo para validar 975 paradas pendientes
- **v4:** Agregar paradas intermedias faltantes
- **v5:** Integrar horarios reales de operadores
- **v6:** Optimizar con datos de frecuencias reales

---

## 7. RESPONSABILIDADES

### Equipo Técnico
- Generación de archivos GTFS
- Validación técnica del feed
- Documentación de procesos

### Pendiente (Operadores/Campo)
- Validación de paradas pendientes
- Horarios y frecuencias reales
- Información de tarifas
- Puntos de venta/recarga

---

## Notas Finales

Este documento define la política para GTFS v2, que busca ser **realista y funcional** con los datos disponibles. No es perfecto, pero es un punto de partida sólido para el sistema de transporte de Trujillo.

**Última actualización:** 2025-12-31
