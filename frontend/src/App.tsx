import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { FamilyProvider } from "./context/FamilyContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";

import LoginPage from "./pages/Auth/LoginPage";
import RegisterPage from "./pages/Auth/RegisterPage";
import VerifyEmailPage from "./pages/Auth/VerifyEmailPage";
import TermsPage from "./pages/Auth/TermsPage";
import OnboardingWizard from "./pages/Onboarding/OnboardingWizard";

import Overview from "./pages/ParentDashboard/Overview";
import LimitsPage from "./pages/ParentDashboard/LimitsPage";
import AccessRequestsPage from "./pages/ParentDashboard/AccessRequestsPage";
import QuestsManagePage from "./pages/ParentDashboard/QuestsManagePage";
import CardsPage from "./pages/ParentDashboard/CardsPage";
import ParentNutsPage from "./pages/ParentDashboard/NutsPage";
import AiCommandPage from "./pages/ParentDashboard/AiCommandPage";

import Home from "./pages/ChildDashboard/Home";
import GoalsPage from "./pages/ChildDashboard/GoalsPage";
import NutsPage from "./pages/ChildDashboard/NutsPage";
import QuestsPage from "./pages/ChildDashboard/QuestsPage";
import RequestAccessPage from "./pages/ChildDashboard/RequestAccessPage";
import AiChatPage from "./pages/ChildDashboard/AiChatPage";

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="spinner-wrap">
        <div className="spinner" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "parent" ? "/parent" : "/child"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <FamilyProvider>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/verify" element={<VerifyEmailPage />} />

          <Route
            path="/parent/onboarding"
            element={
              <ProtectedRoute requireRole="parent">
                <OnboardingWizard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent"
            element={
              <ProtectedRoute requireRole="parent">
                <Overview />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent/limits"
            element={
              <ProtectedRoute requireRole="parent">
                <LimitsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent/access-requests"
            element={
              <ProtectedRoute requireRole="parent">
                <AccessRequestsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent/quests"
            element={
              <ProtectedRoute requireRole="parent">
                <QuestsManagePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent/cards"
            element={
              <ProtectedRoute requireRole="parent">
                <CardsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent/nuts"
            element={
              <ProtectedRoute requireRole="parent">
                <ParentNutsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/parent/ai-command"
            element={
              <ProtectedRoute requireRole="parent">
                <AiCommandPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/child"
            element={
              <ProtectedRoute requireRole={["child", "teen"]}>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/child/goals"
            element={
              <ProtectedRoute requireRole={["child", "teen"]}>
                <GoalsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/child/nuts"
            element={
              <ProtectedRoute requireRole={["child", "teen"]}>
                <NutsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/child/quests"
            element={
              <ProtectedRoute requireRole={["child", "teen"]}>
                <QuestsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/child/request-access"
            element={
              <ProtectedRoute requireRole={["child", "teen"]}>
                <RequestAccessPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/child/ai-chat"
            element={
              <ProtectedRoute requireRole={["child", "teen"]}>
                <AiChatPage />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </FamilyProvider>
    </AuthProvider>
  );
}
