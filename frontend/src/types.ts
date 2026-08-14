/** Shapes returned by the API. These mirror the Pydantic response models in
 *  backend/app/schemas, and are the only place the wire format is described. */

export type Role = "admin" | "member";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
