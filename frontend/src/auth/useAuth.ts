import { useContext } from "react";

import { AuthContext, type AuthState } from "@/auth/AuthContext";

/** Reading auth outside the provider is a wiring mistake, so this throws rather
 *  than returning a null session that would look like "signed out". */
export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
