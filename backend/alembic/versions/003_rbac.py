"""003 — create rol, permiso, rol_permiso tables + seed data

Revision ID: 003
Revises: 002
Create Date: 2026-06-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "permiso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(80), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permiso")),
        sa.UniqueConstraint("codigo", name=op.f("uq_permiso_codigo")),
    )

    op.create_table(
        "rol",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rol")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_rol_tenant_id"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id", "nombre", name=op.f("uq_rol_nombre"),
        ),
    )
    op.create_index(
        op.f("ix_rol_tenant_id"), "rol", ["tenant_id"],
    )

    op.create_table(
        "rol_permiso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rol_id", sa.Uuid(), nullable=False),
        sa.Column("permiso_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rol_permiso")),
        sa.ForeignKeyConstraint(
            ["rol_id"],
            ["rol.id"],
            name=op.f("fk_rol_permiso_rol_id"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permiso_id"],
            ["permiso.id"],
            name=op.f("fk_rol_permiso_permiso_id"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "rol_id", "permiso_id", name=op.f("uq_rol_permiso"),
        ),
    )

    _seed_roles()
    _seed_permisos()
    _seed_rol_permisos()


def downgrade() -> None:
    op.drop_table("rol_permiso")
    op.drop_table("rol")
    op.drop_table("permiso")


def _seed_roles() -> None:
    op.execute(
        sa.text(
            "INSERT INTO rol (id, tenant_id, nombre, descripcion) "
            "SELECT gen_random_uuid(), t.id, 'ALUMNO', 'Alumno — puede ver su estado académico y reservar evaluaciones' "
            "FROM tenant t "
            "WHERE NOT EXISTS (SELECT 1 FROM rol r WHERE r.nombre = 'ALUMNO' AND r.tenant_id = t.id)",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO rol (id, tenant_id, nombre, descripcion) "
            "SELECT gen_random_uuid(), t.id, 'TUTOR', 'Tutor — seguimiento de alumnos atrasados y entregas' "
            "FROM tenant t "
            "WHERE NOT EXISTS (SELECT 1 FROM rol r WHERE r.nombre = 'TUTOR' AND r.tenant_id = t.id)",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO rol (id, tenant_id, nombre, descripcion) "
            "SELECT gen_random_uuid(), t.id, 'PROFESOR', 'Profesor — gestiona calificaciones, encuentros y comunicaciones' "
            "FROM tenant t "
            "WHERE NOT EXISTS (SELECT 1 FROM rol r WHERE r.nombre = 'PROFESOR' AND r.tenant_id = t.id)",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO rol (id, tenant_id, nombre, descripcion) "
            "SELECT gen_random_uuid(), t.id, 'COORDINADOR', 'Coordinador — supervisa comunicaciones y equipos docentes' "
            "FROM tenant t "
            "WHERE NOT EXISTS (SELECT 1 FROM rol r WHERE r.nombre = 'COORDINADOR' AND r.tenant_id = t.id)",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO rol (id, tenant_id, nombre, descripcion) "
            "SELECT gen_random_uuid(), t.id, 'NEXO', 'Nexo — rol administrativo con permisos asignados por tenant' "
            "FROM tenant t "
            "WHERE NOT EXISTS (SELECT 1 FROM rol r WHERE r.nombre = 'NEXO' AND r.tenant_id = t.id)",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO rol (id, tenant_id, nombre, descripcion) "
            "SELECT gen_random_uuid(), t.id, 'ADMIN', 'Administrador — acceso completo a la gestión del tenant' "
            "FROM tenant t "
            "WHERE NOT EXISTS (SELECT 1 FROM rol r WHERE r.nombre = 'ADMIN' AND r.tenant_id = t.id)",
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO rol (id, tenant_id, nombre, descripcion) "
            "SELECT gen_random_uuid(), t.id, 'FINANZAS', 'Finanzas — gestión de liquidaciones y facturación' "
            "FROM tenant t "
            "WHERE NOT EXISTS (SELECT 1 FROM rol r WHERE r.nombre = 'FINANZAS' AND r.tenant_id = t.id)",
        ),
    )


def _seed_permisos() -> None:
    permisos = [
        ("estado_academico:ver", "Ver estado académico propio"),
        ("evaluacion:reservar", "Reservar instancia de evaluación"),
        ("aviso:confirmar", "Confirmar avisos (acknowledgment)"),
        ("calificaciones:importar", "Importar calificaciones"),
        ("atrasados:ver", "Ver alumnos atrasados"),
        ("entregas:detectar_sin_corregir", "Detectar entregas sin corregir"),
        ("comunicacion:enviar", "Enviar comunicaciones a alumnos"),
        ("comunicacion:aprobar", "Aprobar comunicaciones masivas"),
        ("encuentros:gestionar", "Gestionar encuentros"),
        ("guardias:registrar", "Registrar guardias"),
        ("tareas:gestionar", "Gestionar tareas internas"),
        ("avisos:publicar", "Publicar avisos"),
        ("equipos:asignar", "Gestionar equipos docentes"),
        ("estructura:gestionar", "Gestionar estructura académica"),
        ("usuarios:gestionar", "Gestionar usuarios del tenant"),
        ("auditoria:ver", "Ver auditoría"),
        ("impersonacion:usar", "Usar impersonación"),
        ("tenant:configurar", "Configurar el tenant"),
        ("liquidaciones:operar_grilla", "Operar grilla salarial"),
        ("liquidaciones:calcular_cerrar", "Calcular y cerrar liquidaciones"),
        ("facturas:gestionar", "Gestionar facturas"),
    ]
    for codigo, descripcion in permisos:
        op.execute(
            sa.text(
                "INSERT INTO permiso (id, codigo, descripcion) "
                "SELECT gen_random_uuid(), :codigo, :descripcion "
                "WHERE NOT EXISTS (SELECT 1 FROM permiso p WHERE p.codigo = :codigo2)",
            ).bindparams(codigo=codigo, descripcion=descripcion, codigo2=codigo),
        )


def _seed_rol_permisos() -> None:
    mapping = {
        "ALUMNO": ["estado_academico:ver", "evaluacion:reservar", "aviso:confirmar"],
        "TUTOR": [
            "aviso:confirmar",
            "atrasados:ver",
            "entregas:detectar_sin_corregir",
            "encuentros:gestionar",
            "guardias:registrar",
        ],
        "PROFESOR": [
            "aviso:confirmar",
            "calificaciones:importar",
            "atrasados:ver",
            "entregas:detectar_sin_corregir",
            "comunicacion:enviar",
            "encuentros:gestionar",
            "guardias:registrar",
            "tareas:gestionar",
        ],
        "COORDINADOR": [
            "aviso:confirmar",
            "calificaciones:importar",
            "atrasados:ver",
            "entregas:detectar_sin_corregir",
            "comunicacion:enviar",
            "comunicacion:aprobar",
            "encuentros:gestionar",
            "guardias:registrar",
            "tareas:gestionar",
            "avisos:publicar",
            "equipos:asignar",
            "auditoria:ver",
        ],
        "ADMIN": [
            "aviso:confirmar",
            "calificaciones:importar",
            "atrasados:ver",
            "entregas:detectar_sin_corregir",
            "comunicacion:enviar",
            "comunicacion:aprobar",
            "encuentros:gestionar",
            "guardias:registrar",
            "tareas:gestionar",
            "avisos:publicar",
            "equipos:asignar",
            "estructura:gestionar",
            "usuarios:gestionar",
            "auditoria:ver",
            "tenant:configurar",
            "impersonacion:usar",
        ],
        "FINANZAS": [
            "aviso:confirmar",
            "auditoria:ver",
            "liquidaciones:operar_grilla",
            "liquidaciones:calcular_cerrar",
            "facturas:gestionar",
        ],
    }
    for rol_nombre, permiso_codigos in mapping.items():
        for permiso_codigo in permiso_codigos:
            op.execute(
                sa.text(
                    "INSERT INTO rol_permiso (id, rol_id, permiso_id) "
                    "SELECT gen_random_uuid(), r.id, p.id "
                    "FROM rol r, permiso p "
                    "WHERE r.nombre = :rol_nombre "
                    "AND p.codigo = :permiso_codigo "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM rol_permiso rp "
                    "  WHERE rp.rol_id = r.id AND rp.permiso_id = p.id"
                    ")",
                ).bindparams(rol_nombre=rol_nombre, permiso_codigo=permiso_codigo),
            )
