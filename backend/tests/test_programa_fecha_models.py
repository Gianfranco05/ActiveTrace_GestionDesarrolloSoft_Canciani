import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import inspect

from app.core.database import Base
from app.models.base import BaseModelMixin


class TestProgramaMateriaModel:
    def test_table_name(self):
        from app.models.programa_materia import ProgramaMateria
        assert ProgramaMateria.__tablename__ == "programa_materia"

    def test_inherits_base_model_mixin(self):
        from app.models.programa_materia import ProgramaMateria
        instance = ProgramaMateria()
        assert hasattr(instance, "id")
        assert hasattr(instance, "tenant_id")
        assert hasattr(instance, "created_at")
        assert hasattr(instance, "updated_at")
        assert hasattr(instance, "deleted_at")
        assert issubclass(ProgramaMateria, BaseModelMixin)

    def test_inherits_base_declarative(self):
        from app.models.programa_materia import ProgramaMateria
        assert issubclass(ProgramaMateria, Base)

    def test_columns_exist(self):
        from app.models.programa_materia import ProgramaMateria
        mapper = inspect(ProgramaMateria)
        columns = {c.key for c in mapper.columns}
        expected = {
            "id", "tenant_id", "created_at", "updated_at", "deleted_at",
            "materia_id", "carrera_id", "cohorte_id", "titulo",
            "referencia_archivo", "cargado_at",
        }
        assert expected.issubset(columns)

    def test_fk_columns(self):
        from app.models.programa_materia import ProgramaMateria
        mapper = inspect(ProgramaMateria)
        fks = {c.key for c in mapper.columns if c.foreign_keys}
        assert "materia_id" in fks
        assert "carrera_id" in fks
        assert "cohorte_id" in fks
        assert "tenant_id" in fks

    def test_relationships_exist(self):
        from app.models.programa_materia import ProgramaMateria
        mapper = inspect(ProgramaMateria)
        rels = {r.key for r in mapper.relationships}
        assert "materia" in rels
        assert "carrera" in rels
        assert "cohorte" in rels

    def test_relationships_lazy_loading(self):
        from app.models.programa_materia import ProgramaMateria
        mapper = inspect(ProgramaMateria)
        rel_materia = mapper.relationships.materia
        assert rel_materia.lazy == "selectin"
        rel_carrera = mapper.relationships.carrera
        assert rel_carrera.lazy == "selectin"
        rel_cohorte = mapper.relationships.cohorte
        assert rel_cohorte.lazy == "selectin"


class TestFechaAcademicaModel:
    def test_table_name(self):
        from app.models.fecha_academica import FechaAcademica
        assert FechaAcademica.__tablename__ == "fecha_academica"

    def test_inherits_base_model_mixin(self):
        from app.models.fecha_academica import FechaAcademica
        instance = FechaAcademica()
        assert hasattr(instance, "id")
        assert hasattr(instance, "tenant_id")
        assert hasattr(instance, "created_at")
        assert hasattr(instance, "updated_at")
        assert hasattr(instance, "deleted_at")
        assert issubclass(FechaAcademica, BaseModelMixin)

    def test_inherits_base_declarative(self):
        from app.models.fecha_academica import FechaAcademica
        assert issubclass(FechaAcademica, Base)

    def test_columns_exist(self):
        from app.models.fecha_academica import FechaAcademica
        mapper = inspect(FechaAcademica)
        columns = {c.key for c in mapper.columns}
        expected = {
            "id", "tenant_id", "created_at", "updated_at", "deleted_at",
            "materia_id", "cohorte_id", "tipo", "numero", "periodo",
            "fecha", "titulo",
        }
        assert expected.issubset(columns)

    def test_fk_columns(self):
        from app.models.fecha_academica import FechaAcademica
        mapper = inspect(FechaAcademica)
        fks = {c.key for c in mapper.columns if c.foreign_keys}
        assert "materia_id" in fks
        assert "cohorte_id" in fks
        assert "tenant_id" in fks

    def test_relationships_exist(self):
        from app.models.fecha_academica import FechaAcademica
        mapper = inspect(FechaAcademica)
        rels = {r.key for r in mapper.relationships}
        assert "materia" in rels
        assert "cohorte" in rels

    def test_relationships_lazy_loading(self):
        from app.models.fecha_academica import FechaAcademica
        mapper = inspect(FechaAcademica)
        rel_materia = mapper.relationships.materia
        assert rel_materia.lazy == "selectin"
        rel_cohorte = mapper.relationships.cohorte
        assert rel_cohorte.lazy == "selectin"
