from pydantic import BaseModel


class TemplateVariables(BaseModel):
    nombre: str = ""
    apellidos: str = ""
    email: str = ""
    materia: str = ""
    comision: str | None = None
    cohorte: str | None = None


def render_template(template: str, vars: TemplateVariables) -> str:
    result = template
    for field, value in vars.model_dump(exclude_none=True).items():
        result = result.replace(f"{{{{{field}}}}}", str(value))
    return result
