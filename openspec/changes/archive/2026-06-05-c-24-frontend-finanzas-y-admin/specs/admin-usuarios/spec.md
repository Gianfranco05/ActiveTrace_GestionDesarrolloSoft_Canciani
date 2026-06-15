## ADDED Requirements

### Requirement: Listado de usuarios del tenant con filtros
El sistema SHALL mostrar una tabla paginada de usuarios del tenant con filtros y busqueda.

#### Scenario: Acceso a gestion de usuarios
- **WHEN** un usuario con permiso `usuarios:gestionar` navega a `/admin/usuarios`
- **THEN** el sistema muestra una tabla con columnas: nombre, email, roles, estado, ultimo acceso
- **AND** filtros disponibles: rol, estado (activo/inactivo), busqueda por nombre o email

#### Scenario: Filtrar por rol
- **WHEN** el usuario selecciona un rol en el filtro
- **THEN** la tabla muestra solo usuarios con ese rol asignado

### Requirement: Alta de nuevo usuario
El sistema SHALL permitir crear un nuevo usuario en el tenant con roles asignados.

#### Scenario: Crear nuevo usuario
- **WHEN** el usuario completa el formulario con nombre, apellido, email, roles y opcionalmente datos bancarios
- **AND** hace submit
- **THEN** el sistema crea el usuario y envia invitacion por email
- **AND** muestra confirmacion
- **AND** la tabla se actualiza

#### Scenario: Validacion de email duplicado
- **WHEN** el usuario intenta crear un usuario con un email ya registrado en el tenant
- **THEN** el sistema muestra error: "Ya existe un usuario con ese email"

### Requirement: Edicion y activacion/desactivacion de usuario
El sistema SHALL permitir editar datos y cambiar el estado de activacion de un usuario existente.

#### Scenario: Editar usuario
- **WHEN** el usuario modifica nombre, roles o datos bancarios de un usuario existente
- **AND** hace submit
- **THEN** el sistema actualiza el registro

#### Scenario: Desactivar usuario
- **WHEN** el usuario cambia el estado de un usuario a inactivo
- **THEN** el sistema desactiva el acceso del usuario sin eliminar sus datos
- **AND** muestra confirmacion
