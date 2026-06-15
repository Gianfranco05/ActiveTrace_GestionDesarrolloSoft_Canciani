from pydantic import BaseModel, ConfigDict, field_validator


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class Login2FARequiredResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requires_2fa: bool = True
    session_token: str


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class RefreshResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class ForgotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str


class ForgotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = "If the email exists, a reset link has been sent"


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class Enroll2FAResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    secret_base32: str
    qr_uri: str


class Verify2FARequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    totp_code: str


class VerifyLogin2FARequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_token: str
    totp_code: str


class Disable2FARequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str


class MeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: str
    tenant_id: str
    nombre: str
    apellidos: str
    roles: list[str]
    permissions: list[str]
