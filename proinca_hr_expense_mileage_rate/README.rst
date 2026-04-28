===================================
PROINCA - HR Expense Mileage Rate
===================================

Resumen
=======

Este módulo automatiza el cálculo del precio por kilómetro en los gastos de
empleado de Odoo según la categoría de kilometraje asignada al empleado,
el producto utilizado en el gasto, la empresa y la fecha del gasto.

Su objetivo es evitar errores manuales al informar kilometraje y asegurar que
cada gasto se valore con la tarifa vigente que corresponda.

Qué hace el módulo
==================

Cuando un usuario crea un gasto con un producto de gasto que tiene tarifas de
kilometraje configuradas, el módulo:

- identifica la categoría de kilometraje del empleado,
- busca la tarifa válida para esa categoría,
- tiene en cuenta la empresa y la fecha del gasto,
- aplica automáticamente el precio por kilómetro al gasto.

Si se modifica el empleado, el producto, la fecha o la empresa, el importe se
recalcula automáticamente siempre que siga siendo un gasto de kilometraje.

Perfiles implicados
===================

Gestor de Tarifas de Kilometraje
--------------------------------

El grupo ``Gestor de Tarifas de Kilometraje`` puede:

- acceder al menú de configuración ``Gastos > Configuración > Kilometraje PROINCA``,
- crear y mantener categorías de kilometraje,
- crear y mantener tarifas por categoría,
- asignar la categoría de kilometraje en la ficha del empleado.

Usuarios de gastos
------------------

Los usuarios habituales de gastos no necesitan configurar tarifas.
Su trabajo consiste únicamente en registrar el gasto de kilometraje usando el
producto correcto.

Configuración inicial
=====================

Para que el módulo funcione correctamente hay que completar esta configuración.

1. Crear las categorías de kilometraje
--------------------------------------

Ruta:

``Gastos > Configuración > Kilometraje PROINCA > Categorías``

Cree una categoría por cada convenio, grupo o criterio interno que deba tener
una tarifa distinta. Ejemplos:

- Consultoría
- Técnico
- Comercial

Campos principales:

- ``Nombre``: identificador de la categoría.
- ``Descripción``: explicación interna opcional.
- ``Activo``: permite archivar la categoría sin borrarla.

2. Usar un producto de gasto
----------------------------

Ruta:

``Inventario/Ventas > Productos > Productos``

Abra el producto que se utilizará para registrar el kilometraje y confirme que
está marcado con el campo estándar de Odoo:

- ``Puede ser un gasto``

Importante:

- el cálculo automático solo se aplica a productos de gasto que además tengan
  tarifas de kilometraje configuradas,
- los demás productos de gasto siguen funcionando con el comportamiento normal
  de Odoo.

3. Asignar la categoría al empleado
-----------------------------------

Ruta:

``Empleados > Empleados``

En la ficha del empleado, el gestor debe informar el campo:

- ``Categoría de kilometraje``

Sin esta asignación, el empleado no podrá registrar gastos de kilometraje con
tarifa configurada.

4. Crear las tarifas
--------------------

Ruta:

``Gastos > Configuración > Kilometraje PROINCA > Tarifas``

Cada tarifa define cuánto se paga por kilómetro para una combinación concreta
de:

- empresa,
- categoría,
- producto,
- período de vigencia.

Campos principales:

- ``Empresa``
- ``Categoría``
- ``Producto``
- ``Precio por km (€)``
- ``Válido desde``
- ``Válido hasta``
- ``Activo``
- ``Notas``

Recomendaciones:

- utilice una tarifa abierta sin fechas solo cuando quiera que sea la tarifa
  general por defecto,
- si cambia el importe en una fecha determinada, cree una nueva tarifa con el
  nuevo rango de vigencia,
- evite solapes entre fechas para la misma empresa, categoría y producto.

Funcionamiento para el usuario
==============================

Registrar un gasto de kilometraje
---------------------------------

Ruta habitual:

``Gastos > Mis gastos > Crear``

Pasos:

1. Crear un nuevo gasto.
2. Seleccionar el empleado.
3. Elegir el producto de gasto con tarifa de kilometraje.
4. Informar la fecha del gasto.
5. Introducir la cantidad en kilómetros.
6. Guardar.

Qué ocurre automáticamente:

- Odoo localiza la categoría de kilometraje del empleado.
- Busca la tarifa válida para ese producto, empresa y fecha.
- Calcula el precio por km.
- Calcula el importe total del gasto.

Ejemplo:

- tarifa vigente: ``0,27 €/km``
- cantidad informada: ``100``
- total calculado: ``27,00 €``

Recalculo automático
--------------------

El módulo recalcula el gasto si cambia alguno de estos datos:

- producto,
- empleado,
- fecha,
- empresa.

Esto evita que el gasto conserve un precio antiguo cuando cambia una condición
que afecta a la tarifa.

Reglas de negocio importantes
=============================

El módulo aplica estas validaciones:

1. Un empleado con gasto de kilometraje debe tener categoría asignada.
2. Debe existir una tarifa válida para la fecha del gasto.
3. No puede haber tarifas solapadas para la misma empresa, categoría y producto.
4. El precio por km no puede ser negativo.
5. Los productos de gasto sin tarifas de kilometraje no se recalculan.
6. En multicompañía, cada empresa usa sus propias tarifas.

Mensajes de error más habituales
================================

"El empleado no tiene asignada una categoría de kilometraje"
------------------------------------------------------------

Causa:

- el empleado no tiene informada la categoría en su ficha.

Qué hacer:

- pedir al responsable de RRHH o administración que complete la categoría del
  empleado.

"No existe tarifa de kilometraje válida"
----------------------------------------

Causa:

- no hay una tarifa activa para la combinación de empresa, categoría, producto
  y fecha del gasto.

Qué hacer:

- revisar la configuración de tarifas,
- comprobar fechas de vigencia,
- confirmar que se ha usado el producto correcto.

"Se encontraron tarifas solapadas"
----------------------------------

Causa:

- existen dos o más tarifas activas que coinciden en fechas para la misma
  combinación.

Qué hacer:

- corregir la vigencia de las tarifas para que no se solapen.

Buenas prácticas recomendadas
=============================

- Mantener una categoría por criterio real de negocio, no por empleado.
- Utilizar nombres claros en categorías y productos.
- Revisar las tarifas antes de cambios de convenio o cierre de año.
- Archivar tarifas antiguas cuando ya no deban usarse.
- Verificar especialmente la empresa activa en entornos multicompañía.

Limitaciones y alcance
======================

- El módulo solo actúa sobre gastos con productos de gasto que tengan tarifas
  de kilometraje configuradas.
- La categoría de kilometraje del empleado está pensada para gestión interna y
  solo es editable por el grupo responsable.
- La tarifa se determina por empresa, categoría, producto y fecha; no existen
  reglas adicionales por departamento, proyecto o centro de coste.
- Si la configuración no está completa, el gasto no podrá validarse.

Qué se ha validado funcionalmente
=================================

Se ha comprobado mediante pruebas automáticas que el módulo cubre, entre otros,
estos escenarios:

- creación de categorías y tarifas,
- validación de fechas de vigencia,
- prevención de solapes,
- cálculo automático del precio al crear el gasto,
- recálculo al cambiar el empleado,
- error cuando el empleado no tiene categoría,
- error cuando no existe tarifa,
- aislamiento de tarifas por empresa,
- exclusión de productos de gasto sin tarifas de kilometraje.

Soporte interno
===============

Si un usuario no puede registrar correctamente un gasto de kilometraje, conviene
revisar en este orden:

1. el producto usado en el gasto,
2. la categoría de kilometraje del empleado,
3. la empresa del gasto,
4. la fecha del gasto,
5. la vigencia y estado de la tarifa.

