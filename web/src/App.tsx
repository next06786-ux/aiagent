import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { LoadingOrbit } from './components/common/LoadingOrbit';
import { AuthPage } from './pages/AuthPage';
import { HomePage } from './pages/HomePage';
import { AIChatPage } from './pages/AIChatPage';
import { DecisionWorkbenchPage } from './pages/DecisionWorkbenchPage';
import { DecisionHistoryPage } from './pages/DecisionHistoryPage';
import { DecisionSimulationPage } from './pages/DecisionSimulationPage';
import { ModulesPage } from './pages/ModulesPage';
import { ProfilePage } from './pages/ProfilePage';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage';
import SmartInsightsPage from './pages/SmartInsightsPage';
import LoRATrainingPage from './pages/LoRATrainingPage';
import LearningProgressPage from './pages/LearningProgressPage';
import ParallelLifePage from './pages/ParallelLifePage';
import EmergencePatternsPage from './pages/EmergencePatternsPage';
import LifeDomainInsightsPage from './pages/LifeDomainInsightsPage';
import MetaAgentPage from './pages/MetaAgentPage';
import EmergenceDashboardPage from './pages/EmergenceDashboardPage';
import DashboardPage from './pages/DashboardPage';
import RelationshipDecisionPage from './pages/RelationshipDecisionPage';

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="app-loading-screen">
        <LoadingOrbit />
        <h2>正在同步 LifeSwarm Web</h2>
        <p>加载账号状态、主题和后端连接信息...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return <Outlet />;
}

function AuthOnlyRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="app-loading-screen">
        <LoadingOrbit />
        <h2>正在验证账号</h2>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <AuthPage />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthOnlyRoute />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/chat" element={<AIChatPage />} />
        <Route path="/decision" element={<DecisionWorkbenchPage />} />
        <Route path="/decision/history" element={<DecisionHistoryPage />} />
        <Route path="/decision/simulation" element={<DecisionSimulationPage />} />
        <Route path="/modules" element={<ModulesPage />} />
        <Route path="/relationship" element={<RelationshipDecisionPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />
        <Route path="/insights" element={<SmartInsightsPage />} />
        <Route path="/lora-training" element={<LoRATrainingPage />} />
        <Route path="/learning-progress" element={<LearningProgressPage />} />
        <Route path="/parallel-life" element={<ParallelLifePage />} />
        <Route path="/emergence-patterns" element={<EmergencePatternsPage />} />
        <Route path="/life-domain-insights" element={<LifeDomainInsightsPage />} />
        <Route path="/meta-agent" element={<MetaAgentPage />} />
        <Route path="/emergence-dashboard" element={<EmergenceDashboardPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
