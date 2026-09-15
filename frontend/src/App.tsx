import { Navigate, Route, Routes } from 'react-router-dom'
import { Navbar } from './components/Navbar'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Dashboard } from './pages/Dashboard'
import { Interpretation } from './pages/Interpretation'
import { LessonDetail } from './pages/LessonDetail'
import { LessonPath } from './pages/LessonPath'
import { Login } from './pages/Login'
import { QuestDetail } from './pages/QuestDetail'
import { Quests } from './pages/Quests'
import { Recognition } from './pages/Recognition'
import { Signup } from './pages/Signup'
import { useAuth } from './store/AuthContext'

function App() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen">
      <Navbar />
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/learn" replace /> : <Login />} />
        <Route path="/signup" element={user ? <Navigate to="/learn" replace /> : <Signup />} />
        <Route
          path="/learn"
          element={
            <ProtectedRoute>
              <LessonPath />
            </ProtectedRoute>
          }
        />
        <Route
          path="/learn/:lessonId"
          element={
            <ProtectedRoute>
              <LessonDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/recognize"
          element={
            <ProtectedRoute>
              <Recognition />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interpret"
          element={
            <ProtectedRoute>
              <Interpretation />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/quests"
          element={
            <ProtectedRoute>
              <Quests />
            </ProtectedRoute>
          }
        />
        <Route
          path="/quests/:questKey"
          element={
            <ProtectedRoute>
              <QuestDetail />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to={user ? '/learn' : '/login'} replace />} />
      </Routes>
    </div>
  )
}

export default App
