import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { RealtimeProvider } from './hooks/useRealtime'
import { ChatPage } from './pages/ChatPage'
import { ComparisonPage } from './pages/ComparisonPage'
import { ConceptsPage } from './pages/ConceptsPage'
import { DashboardPage } from './pages/DashboardPage'
import { ExperimentsPage } from './pages/ExperimentsPage'
import { HistoryPage } from './pages/HistoryPage'
import { IpcPage } from './pages/IpcPage'
import { MlPage } from './pages/MlPage'
import { ProcessesPage } from './pages/ProcessesPage'
import { SettingsPage } from './pages/SettingsPage'

export default function App() {
  return (
    <RealtimeProvider>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="processes" element={<ProcessesPage />} />
          <Route path="ipc" element={<IpcPage />} />
          <Route path="comparison" element={<ComparisonPage />} />
          <Route path="ml" element={<MlPage />} />
          <Route path="experiments" element={<ExperimentsPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="concepts" element={<ConceptsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </RealtimeProvider>
  )
}
