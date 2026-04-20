## Conclusión corta

Sí, **se puede acercar bastante al estándar usando `product.pricelist`**, pero **no es una sustitución 100% “sin código”** porque `hr.expense` **no usa listas de precios de serie**.

Mi recomendación es:

- **Sí replantearlo**, porque te quitaría bastante lógica custom.
- Pero **no usar la pricelist estándar del partner/contacto** tal cual.
- Lo más sensato sería un rediseño **híbrido y cercano al estándar**:
  - usar `product.pricelist` y `product.pricelist.item` como motor de precios,
  - y mantener una capa mínima HR para decidir **qué pricelist aplica a cada empleado**.

---

## Qué hace hoy el módulo actual

Ahora mismo el módulo funciona así:

- en `hr.employee` añade una **categoría de kilometraje**;
- existe un modelo custom `proinca.mileage.rate` con:
  - empresa,
  - categoría,
  - producto,
  - precio por km,
  - fecha desde/hasta,
  - activo;
- en `hr.expense`, si el producto está marcado como kilometraje, el módulo:
  - mira la categoría del empleado,
  - busca la tarifa válida,
  - calcula el importe del gasto.

Eso está en:

- `models/hr_employee.py`
- `models/hr_expense.py`
- `models/proinca_mileage_rate.py`

---

## Qué hace Odoo estándar realmente

En estándar, `hr.expense`:

- **no tiene `pricelist_id`**;
- **no consulta ninguna tarifa de precios** al calcular gastos;
- calcula `price_unit` a partir del producto/coste o del total del gasto.

Y `product.pricelist` en estándar:

- sí existe en `product`,
- sí permite reglas por:
  - producto,
  - categoría,
  - fecha,
  - empresa,
  - cantidad mínima,
- pero está pensada sobre todo para **pricing comercial**.

Además, la pricelist estándar del partner vive en:

- `res.partner.property_product_pricelist`

Eso está orientado a ventas/clientes, no a RRHH.

---

## ¿Se puede hacer con listas de precios de Odoo?

### Sí, técnicamente
Podrías hacer que, al crear/modificar un `hr.expense` de kilometraje:

1. se identifique la pricelist aplicable al empleado,
2. se consulte el precio del producto en esa pricelist para la fecha del gasto,
3. se use ese precio como **precio por km**,
4. se multiplique por la cantidad.

### Pero no “solo configurando”
Necesitas igualmente una personalización para:

- enlazar empleado → pricelist,
- invocar la pricelist desde `hr.expense`,
- lanzar errores si falta pricelist o regla.

O sea: **sí reutilizas el motor estándar de precios**, pero **sigues necesitando un puente custom en HR Expenses**.

---

## Ventajas frente al módulo actual

## 1. Reutilizas más estándar
En vez de mantener un modelo propio `proinca.mileage.rate`, reutilizas:

- `product.pricelist`
- `product.pricelist.item`

Eso reduce código específico.

## 2. Menos lógica propia de fechas y búsqueda
La vigencia por fecha ya la soporta Odoo en pricelist items.

## 3. Más flexibilidad futura
Si mañana quieres:

- diferentes productos de kilometraje,
- reglas por categoría de producto,
- precios por empresa,
- fechas de vigencia,

la pricelist ya lo soporta bastante bien.

## 4. Mejor interoperabilidad
Importaciones, vistas, búsqueda y mantenimiento de reglas ya están muy resueltos por Odoo.

## 5. Más cercanía conceptual a estándar
Pasas de “modelo custom de tarifas” a “motor de precios estándar + adaptación HR”.

---

## Inconvenientes frente al módulo actual

## 1. `hr.expense` no está pensado para pricelists
Este es el punto más importante.

Odoo estándar **no conecta gastos con pricelists**.
Así que aunque el motor de precios sea estándar, la aplicación en gastos sigue siendo custom.

## 2. Hay desajuste semántico
Una `product.pricelist` en Odoo se entiende como:

- tarifa comercial,
- precio de venta,
- relación con clientes/partners.

Para kilometraje de empleados, funcionalmente sirve, pero **conceptualmente no encaja perfecto**.

## 3. Riesgo de configuración más confusa
Las pricelists estándar tienen opciones que en RRHH pueden sobrar o confundir:

- descuento,
- fórmula,
- otra pricelist como base,
- cantidad mínima,
- categorías de producto,
- grupos de países.

Para un caso simple de kilometraje, eso puede ser demasiado.

## 4. Peor control de “ambigüedad”
El módulo actual hace algo valioso:
- si hay solapes o ambigüedad, **lanza error**.

Las pricelists estándar no están orientadas a “denunciar solapes” del mismo modo:
- aplican la regla que toque según su lógica y orden,
- pero no necesariamente te avisarán de una configuración “conceptualmente ambigua”.

## 5. Diferencias de modelo de datos
Tu modelo actual tiene:
- `date_from` / `date_to` como fecha,
- `active` por línea.

La pricelist estándar usa:
- `date_start` / `date_end` como **datetime**,
- y no tiene el mismo concepto simple de `active` por línea.

Eso complica la migración 1:1.

---

## El mayor problema de usar la pricelist del partner estándar

La idea de “relacionar el empleado con una tarifa de precios de Odoo” es buena.

Pero **yo no usaría directamente**:

- `employee.work_contact_id.property_product_pricelist`
- ni el pricelist del partner asociado al usuario

porque eso mezcla dos mundos:

- **ventas/comercial**
- **RRHH/reembolso**

Y puedes acabar con efectos laterales raros si ese partner se usa en otros sitios.

### Mejor opción
Añadir un campo específico de HR, por ejemplo:

- en `hr.employee`: una pricelist de kilometraje
- o en la categoría de kilometraje: una pricelist asociada

Así reutilizas el motor estándar sin contaminar la semántica comercial.

---

## Recomendación funcional

## Opción A — Empleado → Pricelist
La más simple conceptualmente:

- cada empleado tiene una `product.pricelist`,
- el gasto de kilometraje toma el precio del producto desde esa pricelist.

### Ventajas
- muy fácil de entender,
- muy cercana a tu idea original,
- elimina categorías si no aportan valor real.

### Inconvenientes
- si muchos empleados comparten convenio, duplicas configuración,
- más mantenimiento si cambian tarifas de grupos completos.

---

## Opción B — Categoría → Pricelist
La que yo veo más equilibrada.

- mantienes `proinca.mileage.category`,
- cada categoría apunta a una `product.pricelist`,
- el empleado sigue teniendo categoría,
- pero desaparece `proinca.mileage.rate`.

### Ventajas
- sigues hablando el lenguaje del negocio: convenio/categoría,
- reutilizas el motor estándar de precios,
- evitas duplicar pricelists empleado a empleado,
- migración más natural desde el diseño actual.

### Inconvenientes
- no simplifica tanto como eliminar la categoría,
- sigue habiendo una pequeña capa custom.

---

## Opción C — Mantener el módulo actual
Tiene sentido si valoras más:

- control estricto,
- mensajes de error específicos,
- modelo muy orientado a RRHH,
- simplicidad funcional para usuarios no técnicos.

### Ventaja clave
El modelo actual está muy alineado con el caso de uso.

### Inconveniente clave
Mantiene más código propio del necesario.

---

## Mi recomendación final

### Recomendación: sí, rediseñarlo
Pero no haría una migración a “pricelist pura” sin más.

### Haría esto:
**mantener una pequeña capa HR y sustituir `proinca.mileage.rate` por `product.pricelist`**.

En otras palabras:

- **sí** a reutilizar `product.pricelist`,
- **no** a depender del pricelist comercial estándar del partner,
- **sí** a un campo específico HR que determine la pricelist aplicable.

### Si queréis máxima simplicidad funcional
- Empleado → Pricelist

### Si queréis máxima mantenibilidad con convenios/grupos
- Categoría → Pricelist
  **Esta es mi favorita** para vuestro caso.

---

## Plan propuesto de rediseño

## Fase 1 — Decisión funcional
Elegir uno de estos dos destinos:

1. **Empleado → Pricelist**
2. **Categoría → Pricelist**

Yo priorizaría **Categoría → Pricelist**.

---

## Fase 2 — Modelo objetivo
### Si elegís Categoría → Pricelist
- mantener `proinca.mileage.category`
- añadir `pricelist_id` en `proinca.mileage.category`
- mantener `proinca_mileage_category_id` en empleado
- dejar de usar `proinca.mileage.rate`

### Si elegís Empleado → Pricelist
- eliminar categoría del flujo
- añadir `proinca_mileage_pricelist_id` en `hr.employee`

---

## Fase 3 — Motor de cálculo en gastos
Modificar `hr.expense` para que:

- detecte producto de kilometraje,
- obtenga la pricelist aplicable,
- consulte el precio del producto para la fecha del gasto,
- asigne el importe al gasto.

Mantener validaciones tipo:

- empleado sin pricelist/categoría,
- producto sin regla válida,
- empresa incorrecta.

---

## Fase 4 — Simplificación de pantallas
Eliminar o dejar obsoleto todo lo relacionado con:

- `proinca.mileage.rate`
- menú de tarifas custom
- formulario/listado de tarifas custom

Y dejar al usuario solo con:

- producto de kilometraje,
- categoría o pricelist en empleado,
- pricelist estándar.

---

## Fase 5 — Migración de datos
Crear migración desde `proinca.mileage.rate` a `product.pricelist.item`.

Aquí hay que definir bien:

- cómo convertir `date_from`/`date_to` a `date_start`/`date_end`,
- qué hacer con `active=False`,
- cómo agrupar tarifas actuales en pricelists nuevas.

---

## Fase 6 — Pruebas
Añadir pruebas para validar:

- cálculo por pricelist,
- cambio de empleado,
- cambio de fecha,
- cambio de empresa,
- ausencia de pricelist,
- ausencia de regla válida.

---

## Fase 7 — Limpieza final
Cuando la migración esté validada:

- retirar el modelo `proinca.mileage.rate`,
- retirar sus vistas,
- retirar menús ya innecesarios,
- actualizar documentación funcional.

---

## Riesgos del rediseño

1. **Migración de datos no trivial**
   Sobre todo por fechas y activación.

2. **Semántica menos “RRHH pura”**
   Pricelist es estándar, sí, pero nace en el mundo de producto/ventas.

3. **Posibles configuraciones demasiado potentes**
   Más flexibilidad también significa más margen de error.

4. **Cambios de UX**
   El usuario tendrá que configurar precios desde pricelists estándar.

---

## Mi decisión si tuviera que hacerlo en este repositorio

Yo haría:

### Camino recomendado
- mantener `proinca.mileage.category`,
- reemplazar `proinca.mileage.rate` por una `product.pricelist` enlazada a la categoría,
- dejar `hr.expense` consumiendo esa pricelist,
- eliminar el menú y vistas custom de tarifas.

### Por qué
Porque es el mejor equilibrio entre:

- cercanía al estándar,
- simplicidad,
- reutilización real,
- mantenimiento futuro.
