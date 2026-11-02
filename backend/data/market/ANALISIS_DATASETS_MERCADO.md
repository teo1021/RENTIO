# Análisis Técnico de Datasets de Mercado Inmobiliario — RENTIO

## 1. Resumen Ejecutivo
Para el módulo de recomendación de canon de arrendamiento y análisis de mercado inmobiliario en Medellín, se dispone de dos fuentes de datos estructuradas en formato CSV:
1. `backend/data/market/precios_arriendo_barrios_detalle_api.csv` (en adelante, **Dataset API / DF1**).
2. `backend/data/market/arriendo_en_medellin_por_barrio_2026_datos.csv` (en adelante, **Dataset Consolidado Medellín / DF2**).

Este documento formaliza la inspección técnica, comparación de registros coincidentes, deduplicación, cobertura, fecha, calidad y limitaciones estadísticas para fundamentar el algoritmo de recomendación de canon mensual.

---

## 2. Inspección Detallada de los Datasets

### 2.1 Dataset 1: `precios_arriendo_barrios_detalle_api.csv`
- **Fecha de los datos**: `2026-10-05` (fecha única en todos los registros).
- **Dimensiones**: 1,619 registros y 20 columnas.
- **Cobertura geográfica**: Nacional multiciudad (17 ciudades colombianas).
  - Medellín: 528 registros
  - Bogotá: 511 registros
  - Cali: 195 registros
  - Bucaramanga: 73 registros
  - Rionegro: 72 registros
  - Otras ciudades (Barranquilla, Cúcuta, Chía, Cartagena, Manizales, Pereira, Madrid, Soacha, Neiva, Ibagué, Villavicencio, Mosquera): 240 registros.
- **Estructura de campos**:
  - `fecha`: Fecha de corte (`2026-10-05`).
  - `ciudad_id`, `ciudad`: Identificador y nombre de la ciudad.
  - `barrio_id`: Slug normalizado del barrio o sector (ej. `laureles`, `castropol`, `el-poblado`).
  - `avisos`: Cantidad total de anuncios de arriendo observados en el sector.
  - `p25`, `mediana`, `p75`: Percentil 25, mediana y percentil 75 del canon mensual en COP.
  - `minimo`, `maximo`: Valores extremos observados en las publicaciones.
  - `con_parqueadero`, `mediana_con_parqueadero`: Cantidad y mediana de precios de avisos con parqueadero.
  - `con_telefono`: Cantidad de avisos con contacto telefónico.
  - `fuentes`: Número de portales inmobiliarios de donde se extrajo la muestra.
  - Desagregación por alcobas:
    - `avisos_1_alcoba`, `mediana_1_alcoba`
    - `avisos_2_alcobas`, `mediana_2_alcobas`
    - `avisos_3mas_alcobas`, `mediana_3mas_alcobas`

### 2.2 Dataset 2: `arriendo_en_medellin_por_barrio_2026_datos.csv`
- **Fecha de los datos**: `2026-10-05` (fecha única).
- **Dimensiones**: 439 registros y 21 columnas.
- **Cobertura geográfica**: Exclusivo para la ciudad de Medellín.
- **Estructura jerárquica (campo `tabla`)**:
  1. `tabla == 'resumen'` (1 registro):
     - Muestra global de Medellín: 90,019 avisos analizados.
     - Mediana global de canon: $4,100,000 COP.
     - Proporción con parqueadero: 73.96% (`pct_con_parqueadero: 0.7396`).
     - Rentabilidad bruta anual mediana estimada: 6.4865%.
  2. `tabla == 'por_alcobas'` (3 registros globales de ciudad):
     - 1 alcoba: 17,384 avisos, mediana $3,200,000 COP.
     - 2 alcobas: 41,235 avisos, mediana $3,850,000 COP.
     - 3 o más alcobas: 73,077 avisos, mediana $4,550,000 COP.
  3. `tabla == 'por_barrio'` (435 registros):
     - Estadísticas desagregadas a nivel de barrio.
     - Incluye el nombre amigable de visualización en la columna `grupo` (ej. "Laureles", "Castropol", "El Tesoro") y el slug en `barrio_id`.
     - Mediana general, p25, p75, y desagregaciones `mediana_1`, `mediana_2`, `mediana_3mas`, `mediana_con_parqueadero`, `pct_parqueadero` y `fuentes`.

---

## 3. Comparación de Registros Coincidentes y Deduplicación

Al cruzar los 528 registros de Medellín en el Dataset 1 contra los 435 registros de barrios en el Dataset 2 por el identificador único `barrio_id`:
- **Barrios compartidos**: Exactamente **435 barrios**.
- **Diferencia estadística**:
  - `|mediana_DF1 - mediana_DF2| = 0.0 COP`
  - `|avisos_DF1 - avisos_DF2| = 0`
  - `|p25_DF1 - p25_DF2| = 0.0 COP`
  - `|p75_DF1 - p75_DF2| = 0.0 COP`
  - `|fuentes_DF1 - fuentes_DF2| = 0`

### Conclusión crítica de deduplicación:
Los dos archivos provienen **de la misma recolección y proceso de muestreo al 05 de octubre de 2026**. **Bajo ninguna circunstancia deben sumarse los avisos ni tratarse como dos fuentes independientes**, pues hacerlo duplicaría artificialmente el tamaño de la muestra e introduciría sesgos graves de estimación.

También hay una inconsistencia dentro del consolidado: el total del resumen de Medellín es 90,019 avisos, mientras que los tres conteos de la tabla por alcobas suman 131,696. Por eso, la referencia de ciudad por alcobas se marca como orientativa y no se presenta como una partición reconciliada del total. El consolidado no reporta cantidad de fuentes para ese nivel, así que el sistema no asigna un número de fuentes en el fallback de ciudad.

### Registros exclusivos del Dataset 1 (93 registros):
El Dataset 1 contiene 93 registros adicionales en Medellín que no están en el desglose de barrios del Dataset 2. Al analizarlos, corresponden a **macrozonas o comunas agregadas** (tales como `el-poblado` con 18,132 avisos, `belen` con 1,985 avisos, `robledo` con 1,127 avisos, `la-america` con 804 avisos, `envigado`, `la-candelaria`, etc.).
Estos 93 registros sirven como **nivel de respaldo (fallback de segundo nivel)** cuando un usuario consulte por una comuna o sector amplio sin especificar un barrio puntual.

---

## 4. Alcance: Qué permiten estimar los datasets y qué NO

### Lo que SÍ permiten estimar con respaldo empírico:
1. **Mediana del canon mensual de mercado por barrio específico**:
   - Ofrece el valor central de oferta (mediana) y el rango intercuartílico representativo (percentil 25 a percentil 75).
2. **Segmentación por cantidad de habitaciones**:
   - Mediana directa para 1 alcoba (`mediana_1`), 2 alcobas (`mediana_2`) y 3 o más alcobas (`mediana_3mas`) cuando la muestra del barrio cuenta con datos suficientes (`avisos >= 5`).
3. **Efecto de parqueadero**:
   - Comparación entre la mediana general del sector y `mediana_con_parqueadero`.
4. **Respaldo jerárquico**:
   - Barrio específico con alcobas $\rightarrow$ Barrio general $\rightarrow$ Comuna/Sector $\rightarrow$ Ciudad Medellín por alcobas. Para el fallback de ciudad solo se comunica la mediana, ya que no hay p25/p75 por segmento y los conteos por alcobas no coinciden con el total del resumen.

### Lo que NO permiten estimar (Limitaciones Críticas):
1. **No son contratos cerrados**:
   - Los datos representan **precios solicitados en avisos de oferta pública (asking prices)**, no precios finales de contratos legalizados. Los CSV no permiten cuantificar la diferencia frente al canon pactado.
2. **No existe desagregación por área ($m^2$) ni por estrato socioeconómico**:
   - Los CSVs **no contienen columnas de área construida, metros cuadrados, ni estrato**. Por consiguiente, **no se deben inventar multiplicadores lineales por $m^2$ ni por estrato** fingiendo que provienen del dataset. Si un modelo aplica fórmulas ad-hoc de estrato, debe quedar estrictamente documentado como heurística y no como dato estadístico del estudio de mercado.
3. **No existe desagregación por tipología arquitectónica**:
   - No hay desglose de apartamentos vs casas vs fincas; la muestra refleja el universo agregado de avisos del sector.
4. **Muestras reducidas en barrios periféricos**:
   - En barrios con menos de 10 avisos o donde `mediana_1` es nula, la dispersión es alta y debe advertirse al propietario el nivel de confianza bajo.

---

## 5. Diseño del Motor de Recomendación de Canon

El motor implementado en el servicio de IA sigue las siguientes reglas rigurosas:
1. **Normalización del Barrio**:
   - Mapeo fonético y textual sin tildes contra los 435 barrios de Medellín (`grupo` y `barrio_id`) y las comunas del dataset.
2. **Selección del Estimador**:
   - Si se dispone del barrio y cantidad de alcobas (1, 2 o $\ge 3$), y dicho segmento tiene muestra (`avisos >= 5`), se toma como precio sugerido la `mediana_{alcobas}`.
   - No hay percentiles segmentados por alcobas. Se presenta la mediana de alcobas y, como contexto, p25/p75 generales del barrio sin reescalarlos. En el fallback por ciudad solo se presenta la mediana porque no hay cuartiles por alcobas.
   - Si `parqueadero == True` y el sector muestra una prima por parqueadero (`mediana_con_parqueadero > mediana`), se incluye la referencia en el análisis comparativo.
3. **Trazabilidad y Metadatos**:
   - Todo resultado generado almacena en base de datos:
     - `metodo`: Nivel de cálculo utilizado.
     - `barrio_id`: Identificador normalizado.
     - `habitaciones`: 1, 2 o 3+.
     - `avisos_muestra`: Tamaño de la muestra de avisos publicados.
     - `fuentes`: Número de portales consultados.
     - `fecha_datos`: `2026-10-05`.
     - `p25`, `mediana`, `p75`: Valores exactos del dataset.
     - `limitaciones`: Advertencias explícitas sobre precios de oferta vs contratos cerrados y ausencia de metraje en la muestra.
