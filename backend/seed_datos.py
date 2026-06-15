"""Siembra datos academicos via API: avisos, calificaciones, coloquios, encuentros, tareas.
Uso: python seed_datos.py
"""
import asyncio, sys, uuid
from datetime import UTC, date, datetime, timedelta
from sqlalchemy import select

from app.core.config import Settings
from app.core.database import create_engine, create_session_factory
from app.models.asignacion import Asignacion
from app.models.aviso import Aviso
from app.models.calificacion import Calificacion, UmbralMateria
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.evaluacion import Evaluacion
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.models.tenant import Tenant
from app.models.tarea import Tarea
from app.models.usuario import Usuario
from app.models.rol import Rol

try:
    settings = Settings()
except Exception:
    sys.exit(1)

engine = create_engine(settings)
factory = create_session_factory(engine)


async def seed() -> None:
    async with factory() as session:
        tenant = (await session.execute(select(Tenant).where(Tenant.slug == "default"))).scalar_one()
        ahora = datetime.now(UTC)
        hoy = date.today()

        # ── AVISOS (5) ──
        prog1 = (await session.execute(select(Materia).where(Materia.codigo == "PROG1", Materia.tenant_id == tenant.id))).scalar_one()
        prof_rol = (await session.execute(select(Rol).where(Rol.nombre == "PROFESOR", Rol.tenant_id == tenant.id))).scalar_one()
        avisos = [
            Aviso(tenant_id=tenant.id, alcance="Global", severidad="Info", titulo="Bienvenida al cuatrimestre MAR-2026", cuerpo="Les damos la bienvenida a todos. Recuerden consultar el cronograma.", inicio_en=ahora - timedelta(days=10), fin_en=ahora + timedelta(days=180), requiere_ack=True),
            Aviso(tenant_id=tenant.id, alcance="Global", severidad="Advertencia", titulo="Feriado 25 de junio", cuerpo="No habra clases el 25 de junio.", inicio_en=ahora - timedelta(days=5), fin_en=ahora + timedelta(days=30), requiere_ack=True),
            Aviso(tenant_id=tenant.id, alcance="PorMateria", materia_id=prog1.id, severidad="Info", titulo="Cambio de aula - Programacion I", cuerpo="Las clases pasan al aula 305.", inicio_en=ahora - timedelta(days=2), fin_en=ahora + timedelta(days=60), requiere_ack=True),
            Aviso(tenant_id=tenant.id, alcance="Global", severidad="Info", titulo="Inscripcion a coloquios abierta", cuerpo="Ya pueden inscribirse a los coloquios de julio.", inicio_en=ahora, fin_en=ahora + timedelta(days=45)),
            Aviso(tenant_id=tenant.id, alcance="PorRol", rol_destino="PROFESOR", severidad="Advertencia", titulo="Carga de notas pendiente", cuerpo="Recuerden cargar las notas antes del viernes.", inicio_en=ahora - timedelta(days=3), fin_en=ahora + timedelta(days=10)),
        ]
        session.add_all(avisos)
        print(f"  [OK] {len(avisos)} avisos")

        # ── ENCUENTROS ──
        ing = (await session.execute(select(Carrera).where(Carrera.codigo == "ING", Carrera.tenant_id == tenant.id))).scalar_one()
        mar_ing = (await session.execute(select(Cohorte).where(Cohorte.nombre == "MAR-2026", Cohorte.carrera_id == ing.id, Cohorte.tenant_id == tenant.id))).scalar_one()
        # Find an asignacion for Programacion I to use as slot's asignacion_id
        asig = (await session.execute(select(Asignacion).where(Asignacion.materia_id == prog1.id, Asignacion.cohorte_id == mar_ing.id, Asignacion.deleted_at.is_(None)).limit(1))).scalar_one()
        from datetime import time as dt_time
        slot = SlotEncuentro(tenant_id=tenant.id, asignacion_id=asig.id, materia_id=prog1.id, titulo="Clase Programacion I", hora=dt_time(18, 0), dia_semana="Miercoles", meet_url="https://meet.google.com/abc-defg-hij")
        session.add(slot)
        await session.flush()
        for s in range(4):
            session.add(InstanciaEncuentro(tenant_id=tenant.id, slot_id=slot.id, materia_id=prog1.id, asignacion_id=asig.id, fecha=hoy + timedelta(days=7*s), hora=dt_time(18, 0), titulo="Clase Programacion I", estado="Programado"))
        print("  [OK] 4 encuentros")

        # ── COLOQUIOS ──
        materias = (await session.execute(select(Materia).where(Materia.tenant_id == tenant.id, Materia.estado == "Activa"))).scalars().all()
        for i, mat in enumerate(materias[:3]):
            session.add(Evaluacion(tenant_id=tenant.id, materia_id=mat.id, cohorte_id=mar_ing.id, tipo="Coloquio", instancia=f"Instancia {i+1} - JUL 2026", cupos_por_dia=[{"fecha": str(hoy + timedelta(days=30+i*7)), "cupo": 10}]))
        print(f"  [OK] 3 coloquios")

        # ── PADRON + CALIFICACIONES ──
        alumno_rol = (await session.execute(select(Rol).where(Rol.nombre == "ALUMNO", Rol.tenant_id == tenant.id))).scalar_one()
        asigns = (await session.execute(select(Asignacion).where(Asignacion.tenant_id == tenant.id, Asignacion.rol_id == alumno_rol.id, Asignacion.materia_id.isnot(None), Asignacion.deleted_at.is_(None)))).scalars().all()
        from collections import defaultdict
        materia_alumnos = defaultdict(list)
        for a in asigns:
            materia_alumnos[a.materia_id].append(a.usuario_id)

        calif_count = 0
        for mat in materias:
            alumnos = materia_alumnos.get(mat.id, [])
            if not alumnos:
                continue
            vp = VersionPadron(tenant_id=tenant.id, materia_id=mat.id)
            session.add(vp)
            await session.flush()
            for al_id in alumnos:
                al_user = (await session.execute(select(Usuario).where(Usuario.id == al_id, Usuario.tenant_id == tenant.id))).scalar_one()
                ent = EntradaPadron(tenant_id=tenant.id, version_id=vp.id, usuario_id=al_user.id, nombre=al_user.nombre, apellidos=al_user.apellidos)
                session.add(ent)
                await session.flush()
                profe_id = asigns[0].usuario_id if asigns else al_id  # fallback
                for act, nota in [("TP1", 8.0), ("TP2", 7.0), ("Parcial 1", 4.0)]:
                    from decimal import Decimal
                    session.add(Calificacion(tenant_id=tenant.id, entrada_padron_id=ent.id, materia_id=mat.id, cohorte_id=mar_ing.id, actividad=act, tipo="Numerica", nota_numerica=Decimal(str(nota)), aprobado=nota >= 6.0, origen="Importado", cargado_por=profe_id))
                    calif_count += 1
            # Umbral
            session.add(UmbralMateria(tenant_id=tenant.id, materia_id=mat.id, umbral_pct=60))
        print(f"  [OK] {calif_count} calificaciones + umbrales")

        # ── TAREAS ──
        profe = (await session.execute(select(Usuario).where(Usuario.tenant_id == tenant.id))).scalars().first()
        if profe:
            for i in range(3):
                session.add(Tarea(tenant_id=tenant.id, materia_id=prog1.id, asignado_a=profe.id, asignado_por=profe.id, descripcion=f"Tarea {i+1}: Revisar entregas TP{i+1}", estado="Pendiente"))
        print("  [OK] 3 tareas")

        await session.commit()
        print("\nDatos sembrados!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())
