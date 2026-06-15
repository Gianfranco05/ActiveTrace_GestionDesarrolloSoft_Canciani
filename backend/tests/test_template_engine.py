"""TDD: TemplateEngine tests."""

from app.services.template_engine import TemplateVariables, render_template


def test_render_substitutes_variables():
    result = render_template(
        "Hola {{nombre}} {{apellidos}}",
        TemplateVariables(nombre="Ana", apellidos="Lopez"),
    )
    assert result == "Hola Ana Lopez"


def test_render_all_defined_variables():
    t = "{{nombre}} {{apellidos}} {{email}} {{materia}} {{comision}} {{cohorte}}"
    v = TemplateVariables(
        nombre="Juan", apellidos="Perez", email="j@t.com",
        materia="Matematica", comision="A", cohorte="2026",
    )
    result = render_template(t, v)
    assert result == "Juan Perez j@t.com Matematica A 2026"


def test_unknown_variables_left_as_is():
    result = render_template(
        "Hola {{nombre}} {{unknown_var}}",
        TemplateVariables(nombre="Ana"),
    )
    assert result == "Hola Ana {{unknown_var}}"


def test_empty_variables_handled_gracefully():
    result = render_template(
        "Hola {{nombre}} {{apellidos}}",
        TemplateVariables(),
    )
    assert result == "Hola  "


def test_template_without_variables_unchanged():
    result = render_template(
        "Mensaje fijo sin variables",
        TemplateVariables(nombre="Ana"),
    )
    assert result == "Mensaje fijo sin variables"


def test_none_field_excluded():
    v = TemplateVariables(nombre="Ana", comision=None)
    result = render_template("{{nombre}} {{comision}}", v)
    assert result == "Ana {{comision}}"
