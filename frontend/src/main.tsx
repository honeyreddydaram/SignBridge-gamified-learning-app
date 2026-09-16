import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { BackendGate } from './components/BackendGate.tsx'
import { AuthProvider } from './store/AuthContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <BackendGate>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BackendGate>
    </BrowserRouter>
  </StrictMode>,
)
