"""Permission code catalog — single source of truth for modulo:accion codes.

Every permission used by ``require_permission()`` and seeded into the DB
MUST be declared here first. Codes follow the pattern ``modulo:accion``.

Added in C-04 (rbac-permisos-finos). Extended in C-18 (liquidaciones-y-honorarios).
"""

PERMISSION_CODES: dict[str, str] = {
    "estado_academico:ver": "Ver estado académico propio",
    "evaluacion:reservar": "Reservar instancia de evaluación",
    "aviso:confirmar": "Confirmar avisos (acknowledgment)",
    "calificaciones:importar": "Importar calificaciones",
    "calificaciones:cargar": "Cargar calificaciones (upload)",
    "calificaciones:ver": "Ver calificaciones",
    "atrasados:ver": "Ver alumnos atrasados",
    "entregas:detectar_sin_corregir": "Detectar entregas sin corregir",
    "comunicacion:enviar": "Enviar comunicaciones a alumnos",
    "comunicacion:aprobar": "Aprobar comunicaciones masivas",
    "encuentros:gestionar": "Gestionar encuentros",
    "guardias:registrar": "Registrar guardias",
    "tareas:gestionar": "Gestionar tareas internas",
    "avisos:publicar": "Publicar avisos",
    "equipos:asignar": "Gestionar equipos docentes",
    "estructura:gestionar": "Gestionar estructura académica",
    "usuarios:gestionar": "Gestionar usuarios del tenant",
    "auditoria:ver": "Ver auditoría",
    "impersonacion:usar": "Usar impersonación",
    "tenant:configurar": "Configurar el tenant",
    "padron:cargar": "Cargar padrón de alumnos",
    "analisis:ver": "Ver análisis y reportes",
    "coloquios:gestionar": "Gestionar coloquios",
    "fechas:gestionar": "Gestionar fechas académicas",
    "programas:gestionar": "Gestionar programas de materia",
    "coloquios:reservar": "Reservar turno de coloquio",
    # ── C-18: Liquidaciones y Honorarios ──
    "liquidaciones:ver": "Ver liquidaciones",
    "liquidaciones:calcular": "Calcular liquidaciones",
    "liquidaciones:cerrar": "Cerrar liquidaciones",
    "liquidaciones:exportar": "Exportar liquidaciones",
    "liquidaciones:configurar-salarios": "Configurar grilla salarial",
    # ── legacy codes preserved for migration compatibility ──
    "liquidaciones:operar_grilla": "Operar grilla salarial (legacy)",
    "liquidaciones:calcular_cerrar": "Calcular y cerrar liquidaciones (legacy)",
    "facturas:gestionar": "Gestionar facturas",
    "perfil:editar": "Editar perfil propio",
    "mensajeria:usar": "Usar mensajería interna",
    # ── C-25: Permisos de coordinación no seedeados previamente ──
    "coordinacion:acceso": "Acceder al dashboard de coordinación",
    "monitores:ver": "Ver panel de monitores de coordinación",
    "coordinacion:setup": "Configurar setup del cuatrimestre",
}
