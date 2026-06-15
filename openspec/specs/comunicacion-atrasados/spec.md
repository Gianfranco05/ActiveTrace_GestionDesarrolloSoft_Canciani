## ADDED Requirements

### Requirement: Vista previa del mensaje

El sistema SHALL mostrar una previsualización del mensaje que se enviará a los alumnos seleccionados, incluyendo asunto y cuerpo con las variables de personalización sustituidas.

#### Scenario: Preview con datos personalizados
- **WHEN** el usuario accede a la vista previa con 2 alumnos seleccionados
- **THEN** se muestran los mensajes previsualizados para cada alumno con nombre y datos sustituidos

#### Scenario: Preview sin alumnos seleccionados
- **WHEN** el usuario accede a la vista de comunicación sin alumnos seleccionados
- **THEN** el sistema muestra un mensaje indicando que debe seleccionar alumnos desde la vista de atrasados

### Requirement: Envío masivo a cola de comunicaciones

El sistema SHALL permitir al PROFESOR enviar los mensajes previsualizados a la cola de comunicaciones, donde cada mensaje queda en estado Pendiente.

#### Scenario: Envío confirmado
- **WHEN** el usuario revisa el preview y confirma el envío
- **THEN** los mensajes se encolan con estado Pendiente y el sistema navega a la vista de tracking

#### Scenario: Cancelación antes de enviar
- **WHEN** el usuario está en la vista previa y decide cancelar
- **THEN** el sistema vuelve a la vista de atrasados sin encolar ningún mensaje

### Requirement: Tracking de estado en tiempo real

El sistema SHALL mostrar el estado de cada comunicación en tiempo real mediante polling, actualizando los estados Pendiente → Enviando → Enviado/Error/Cancelado.

#### Scenario: Transición de estados durante el tracking
- **WHEN** hay comunicaciones en estado Pendiente y el sistema las despacha
- **THEN** la vista de tracking refleja la transición Pendiente → Enviando → Enviado sin necesidad de refresco manual

#### Scenario: Comunicación fallida
- **WHEN** una comunicación pasa a estado Error
- **THEN** la tabla muestra el estado "Error" con un indicador visual rojo y permite ver el detalle del error

#### Scenario: Todas las comunicaciones finalizadas
- **WHEN** todas las comunicaciones del lote están en estado final (Enviado/Error/Cancelado)
- **THEN** el polling se detiene y se muestra un resumen con contadores por estado

### Requirement: Cancelación de envíos pendientes

El sistema SHALL permitir cancelar comunicaciones que aún están en estado Pendiente.

#### Scenario: Cancelación individual
- **WHEN** el usuario hace clic en "Cancelar" sobre una comunicación Pendiente
- **THEN** esa comunicación pasa a estado Cancelado
