/** Route table.
 *
 * Signed-in routes are nested inside one ProtectedRoute wrapping the AppShell,
 * so the gate is declared once rather than repeated per page, and the shell does
 * not remount when moving between sections.
 */
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AppShell } from "@/components/AppShell";
import { AuthProvider } from "@/auth/AuthContext";
import { CreateAccountPage } from "@/pages/CreateAccountPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { OverviewPage } from "@/pages/OverviewPage";
import { ProjectsPage } from "@/pages/ProjectsPage";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { SignInPage } from "@/pages/SignInPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/sign-in" element={<SignInPage />} />
          <Route path="/create-account" element={<CreateAccountPage />} />

          <Route
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<OverviewPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
