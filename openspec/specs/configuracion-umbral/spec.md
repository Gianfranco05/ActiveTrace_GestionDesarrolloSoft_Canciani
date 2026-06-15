## ADDED Requirements

### Requirement: Visualización del umbral actual

El sistema SHALL mostrar el umbral de aprobación configurado para la materia seleccionada, con el valor por defecto de 60% si aún no fue configurado.

#### Scenario: Umbral con valor por defecto
- **WHEN** el usuario accede a la configuración de umbral de una materia que nunca fue configurada
- **THEN** el sistema muestra "60%" como valor actual

#### Scenario: Umbral previamente configurado
- **WHEN** el usuario accede a la configuración de umbral de una materia con umbral configurado en 70%
- **THEN** el sistema muestra "70%" como valor actual

### Requirement: Modificación del umbral de aprobación

El sistema SHALL permitir al PROFESOR modificar el porcentaje de umbral de aprobación para una materia, entre 0% y 100%.

#### Scenario: Configuración de nuevo umbral
- **WHEN** el usuario ingresa "75" como nuevo umbral y confirma
- **THEN** el sistema guarda el umbral y confirma visualmente el cambio

#### Scenario: Valor fuera de rango
- **WHEN** el usuario ingresa "120" como umbral e intenta confirmar
- **THEN** el sistema muestra un error de validación indicando que el valor debe estar entre 0 y 100

#### Scenario: Valor no numérico
- **WHEN** el usuario ingresa texto no numérico en el campo de umbral
- **THEN** el sistema muestra un error de validación indicando que debe ser un número

### Requirement: Efecto del umbral en análisis posteriores

El sistema SHALL indicar al usuario que modificar el umbral afectará los cálculos de atrasados y ranking para esa materia.

#### Scenario: Mensaje informativo al modificar umbral
- **WHEN** el usuario modifica el umbral de una materia que ya tiene calificaciones importadas
- **THEN** el sistema muestra un aviso indicando que los cálculos de atrasados y ranking se recalcularán con el nuevo umbral
