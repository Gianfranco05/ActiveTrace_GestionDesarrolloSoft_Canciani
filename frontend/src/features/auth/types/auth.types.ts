export interface LoginPayload {
  email: string;
  password: string;
}

export interface TwoFactorPayload {
  session_token: string;
  totp_code: string;
}

export interface ForgotPayload {
  email: string;
}

export interface ResetPayload {
  token: string;
  new_password: string;
}
