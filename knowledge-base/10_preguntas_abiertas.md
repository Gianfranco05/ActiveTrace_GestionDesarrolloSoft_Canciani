# 10 — Preguntas Abiertas y Decisiones de Producto Pendientes

> **Propósito**: registrar las decisiones de diseño de producto que aún no están cerradas, ordenadas por impacto sobre el modelo de dominio. Cada ítem es una pregunta genuina que el equipo de producto debe resolver antes de (o durante) la implementación. Las decisiones ya cerradas aparecen en los archivos correspondientes de la KB y en [`docs/ARQUITECTURA.md`](../docs/ARQUITECTURA.md); no se repiten acá. Este archivo es un tablero vivo: cuando una pregunta se cierra, se documenta la resolución en el archivo temático correspondiente y se retira de acá.

---

## Prioridad ALTA — bloqueantes para el modelo de dominio

> **Todas las preguntas de prioridad ALTA fueron resueltas** el 2026-06-08. Las resoluciones están documentadas en los archivos temáticos correspondientes. Ver tabla de "Decisiones ya cerradas" al final de este documento.

---

## Prioridad MEDIA — refinamiento del modelo

### PA-05 — ¿Cómo y desde dónde se crea una guardia?

El módulo de guardias muestra el listado de guardias registradas por docente, pero el flujo de creación no está especificado.

**Preguntas abiertas**:

- ¿Las guardias se crean desde el módulo de encuentros, desde un formulario dedicado, o ambos?
- ¿Quién puede crear una guardia: solo el docente que la cubre, o también el COORDINADOR en su nombre?
- ¿Requiere aprobación posterior?

---

### PA-08 — ¿Cuál es el ciclo de vida de una Tarea?

El módulo de tareas tiene un filtro de estado, pero los valores posibles del ciclo de vida no están definidos.

**Preguntas abiertas**:

- ¿Cuáles son los estados posibles de una tarea? (ej.: `abierta → en progreso → completada → archivada`)
- ¿Las transiciones son libres o tienen reglas (ej.: solo el creador puede cerrarla)?
- ¿Hay notificaciones automáticas al cambiar de estado?

---

### PA-09 — ¿Qué permite la funcionalidad de comunicación por grupos en el módulo de equipos?

Dentro del módulo de equipos docentes existe una funcionalidad de comunicación grupal cuyo alcance no está especificado.

**Preguntas abiertas**:

- ¿Es para enviar mensajes masivos al equipo docente de una comisión?
- ¿O es comunicación entre pares (docentes entre sí)?
- ¿Requiere aprobación previa como las comunicaciones hacia alumnos?

---

### PA-11 — ¿Qué es el "criterio de clasificación" en el monitor general?

El monitor general permite configurar un criterio de clasificación mediante un modal.

**Preguntas abiertas**:

- ¿Qué criterios se pueden configurar? (ej.: por porcentaje de avance, por cantidad de entregas, por calificación promedio)
- ¿La configuración es personal (por usuario) o global (por tenant)?
- ¿Afecta qué alumnos se consideran "atrasados" o es solo una vista?

---

### PA-12 — ¿Qué incluye la vista administrativa de encuentros?

El módulo de encuentros tiene una vista con permisos ampliados respecto a la vista docente estándar.

**Preguntas abiertas**:

- ¿Permite ver y editar los encuentros de todos los docentes de una comisión o de todo el tenant?
- ¿Permite crear encuentros en nombre de otro docente?
- ¿Tiene capacidad de aprobación o solo de consulta?

---

### PA-13 — ¿Qué es el contexto de agrupación de tareas?

El módulo de tareas permite filtrar por un contexto de agrupación cuya semántica no está definida.

**Preguntas abiertas**:

- ¿El contexto de agrupación es una cohorte, una materia, un equipo docente, o algún otro concepto?
- ¿Una tarea puede pertenecer a más de un contexto?

---

### PA-14 — ¿Cómo reserva un alumno una instancia de coloquio?

El sistema muestra reservas activas y cupos disponibles para instancias de evaluación, pero el flujo de reserva del alumno no está especificado.

**Preguntas abiertas**:

- ¿El alumno reserva desde dentro del sistema o desde un canal externo (ej.: Moodle, link público)?
- ¿Hay restricciones para reservar (ej.: cantidad máxima de intentos, estado de regularidad requerido)?
- ¿El alumno puede cancelar su reserva?

---

### PA-15 — ¿El módulo de corrección automática está integrado con las calificaciones?

El sistema contempla la posibilidad de integrar un módulo de corrección automática de actividades.

**Preguntas abiertas**:

- ¿Las calificaciones generadas por el corrector automático se importan al sistema directamente o requieren revisión y aprobación docente?
- ¿El corrector opera sobre entregas ya subidas al sistema o sobre entregas del LMS (Moodle)?
- ¿Cómo se audita una calificación generada automáticamente vs. una ingresada manualmente?

---

### PA-24 — ¿Las facturas se asocian a comisiones o son globales por docente?

En el módulo de facturas existe un campo de detalle con texto libre, pero no está claro si hay una asociación formal con el trabajo realizado.

**Preguntas abiertas**:

- ¿Una factura debe vincularse a una comisión específica, a un período, o puede ser un concepto genérico?
- ¿Cómo se concilia la factura con el cálculo de liquidación?
- ¿El sistema valida que el monto de la factura no supere el total liquidado?

---

## Prioridad BAJA — pulido y definición de detalles

### PA-16 — ¿Cuáles son los niveles de severidad de los avisos y qué efecto tienen?

**Preguntas abiertas**:

- ¿Los valores de severidad son un enumerado fijo (`info`, `advertencia`, `error`) o es configurable?
- ¿La severidad afecta el comportamiento del sistema (ej.: un aviso de error bloquea al alumno hasta que lo confirme)?
- ¿Hay notificaciones adicionales disparadas por severidad?

---

### PA-17 — ¿El tipo de facturación del docente afecta el cálculo de liquidación?

Algunos docentes pueden emitir comprobantes fiscales (ej.: monotributistas), lo cual puede tener implicancias en el cálculo.

**Preguntas abiertas**:

- ¿El tipo de facturación modifica algún concepto del cálculo (ej.: agrega retenciones, modifica la base)?
- ¿O es solo un atributo informativo para el módulo de FINANZAS sin impacto en la fórmula?

---

### PA-18 — ¿El CUIL del docente se calcula automáticamente o se carga manualmente?

**Preguntas abiertas**:

- ¿El sistema calcula el CUIL a partir del DNI aplicando la regla estándar (`prefijo-DNI-dígito verificador`)?
- ¿O el CUIL es un campo de carga manual sin validación automática?
- Si se calcula, ¿qué pasa cuando el CUIL real difiere del calculado (ej.: personas con CUIL de tipo empresa)?

---

### PA-19 — ¿Qué pasa con las asignaciones vigentes cuando se desactiva un docente?

**Preguntas abiertas**:

- ¿Las asignaciones vigentes se cierran automáticamente (se les pone fecha de fin) al desactivar el usuario?
- ¿O quedan en estado inconsistente hasta que el ADMIN las gestione manualmente?
- ¿El sistema emite una alerta al COORDINADOR cuando uno de sus docentes es desactivado?

---

## Decisiones ya cerradas (referencia)

Las siguientes preguntas que existían en versiones anteriores de este documento ya fueron resueltas y su resolución está documentada en los archivos correspondientes:

| Código original | Resolución | Dónde está documentado |
|-----------------|-----------|------------------------|
| PA-01 | Catálogo único de materias: una sola entidad `Materia` cubre tanto el código del plan (`codigo`) como el nombre descriptivo (`nombre`). No existe `InstanciaDictado` separada. La relación con carreras/cohortes se modela vía `Asignacion`. | [04_modelo_de_datos.md §E3](04_modelo_de_datos.md) |
| PA-02 | El rol TUTOR existe formalmente en el catálogo; ver descripción de capacidades | [03_actores_y_roles.md](03_actores_y_roles.md) |
| PA-04 | Login por email + contraseña; 2FA opcional (TOTP); recuperación por token de un solo uso; alta solo administrativa en MVP | [07_flujos_principales.md](07_flujos_principales.md), [`docs/ARQUITECTURA.md` §5.1](../docs/ARQUITECTURA.md) |
| PA-06 | Fórmula de liquidación: Base (por rol) + Plus (por clave × rol); ver RN-31 a RN-38 | [05_reglas_de_negocio.md](05_reglas_de_negocio.md) |
| PA-07 | Las cohortes pertenecen a UNA carrera específica (no transversales). `carrera_id` es obligatoria. Un alumno puede estar en cohortes de distintas carreras si cursa más de una. | [04_modelo_de_datos.md §E2](04_modelo_de_datos.md) |
| PA-21 | Impersonación via parámetro de petición: eliminada. La impersonación legítima requiere permiso explícito, sesión diferenciada y auditoría completa | [03_actores_y_roles.md §4](03_actores_y_roles.md), [`docs/ARQUITECTURA.md`](../docs/ARQUITECTURA.md) |
| PA-22 | Las claves de Plus son configurables por tenant (no hardcodeadas). El mapeo materia→grupo se almacena en `Materia.grupo_plus` (campo nullable). El ADMIN define el mapeo. Materias sin `grupo_plus` no generan Plus. | [04_modelo_de_datos.md §E3 y §E18](04_modelo_de_datos.md) |
| PA-23 | Acumulación lineal por comisión: `N_comisiones × Plus(grupo, rol)`. Sin tope. Misma lógica para todos los roles. Ya estaba definida en RN-33 y RN-34. | [05_reglas_de_negocio.md RN-33](05_reglas_de_negocio.md), [04_modelo_de_datos.md §E18](04_modelo_de_datos.md) |
| PA-25 | NEXO es un rol de enlace administrativo-pedagógico. Acceso de lectura a datos de alumnos (propio), encuentros y guardias propias, auditoría propia. No gestiona equipos ni publica avisos. Puede ser simultáneo con COORDINADOR. | [03_actores_y_roles.md §3.3](03_actores_y_roles.md) |

---

## Cómo cerrar estas preguntas

Para resolver las preguntas pendientes se recomienda:

1. **Una sesión de trabajo con el responsable de producto** — cubre las preguntas de dominio (PA-01, PA-22, PA-23, PA-25 son prioritarias).
2. **Revisión del modelo de datos con el equipo técnico** — para validar las entidades y relaciones de [04_modelo_de_datos.md](04_modelo_de_datos.md).
3. **Sesión de refinamiento con FINANZAS** — para cerrar PA-17, PA-18, PA-24 que afectan el módulo de liquidaciones.
4. **Cuando se cierre una pregunta**: documentar la resolución en el archivo temático correspondiente y moverla a la tabla de "Decisiones ya cerradas" de este archivo.
