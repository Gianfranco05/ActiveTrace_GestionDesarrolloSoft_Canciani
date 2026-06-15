## ADDED Requirements

### Requirement: Upload de archivo de calificaciones

El sistema SHALL permitir al PROFESOR subir un archivo de calificaciones exportado desde el LMS en formato hoja de cálculo (.xlsx, .xls, .csv).

#### Scenario: Upload exitoso de archivo válido
- **WHEN** el usuario selecciona un archivo .xlsx con calificaciones y lo sube
- **THEN** el sistema procesa el archivo y muestra una vista previa de las actividades y alumnos detectados

#### Scenario: Archivo con formato inválido
- **WHEN** el usuario intenta subir un archivo que no es .xlsx, .xls o .csv
- **THEN** el sistema muestra un mensaje de error indicando los formatos permitidos

#### Scenario: Archivo excede tamaño máximo
- **WHEN** el usuario intenta subir un archivo mayor a 20MB
- **THEN** el sistema muestra un mensaje de error indicando el límite de tamaño

### Requirement: Vista previa de actividades detectadas

El sistema SHALL presentar una tabla con las actividades detectadas en el archivo subido, mostrando el nombre de cada actividad y una muestra de los valores detectados.

#### Scenario: Vista previa con múltiples actividades
- **WHEN** el archivo contiene 5 columnas de actividades con valores numéricos
- **THEN** la vista previa muestra las 5 actividades con checkbox para seleccionar cada una

#### Scenario: Vista previa con valores textuales
- **WHEN** el archivo contiene actividades con valores como "Aprobada", "No entregado", "Ausente"
- **THEN** la vista previa muestra estas actividades marcadas como textuales, distinguibles de las numéricas

### Requirement: Selección de actividades para análisis

El sistema SHALL permitir al usuario seleccionar cuáles actividades detectadas incluir en el análisis posterior (atrasados, ranking, notas finales).

#### Scenario: Selección parcial de actividades
- **WHEN** el usuario selecciona 3 de 5 actividades detectadas y confirma
- **THEN** el sistema importa solo las 3 actividades seleccionadas para el análisis

#### Scenario: Ninguna actividad seleccionada
- **WHEN** el usuario intenta confirmar sin seleccionar ninguna actividad
- **THEN** el sistema muestra un mensaje pidiendo que seleccione al menos una actividad

### Requirement: Indicador de progreso durante la importación

El sistema SHALL mostrar una barra de progreso durante la subida y procesamiento del archivo.

#### Scenario: Barra de progreso durante upload
- **WHEN** el archivo se está subiendo
- **THEN** se muestra un indicador de progreso con porcentaje de subida
