import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import About from './pages/About'
import { Login, Register } from './pages/AuthPages'
import Dashboard from './pages/Dashboard'
import Diseases from './pages/Diseases'
import History from './pages/History'
import ImageScreening from './pages/ImageScreening'
import Landing from './pages/Landing'
import Metrics from './pages/Metrics'
import NotFound from './pages/NotFound'
import Result from './pages/Result'
import Screening from './pages/Screening'

const guard = (el) => <ProtectedRoute>{el}</ProtectedRoute>

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/about" element={<About />} />
        <Route path="/dashboard" element={guard(<Dashboard />)} />
        <Route path="/screen" element={guard(<Diseases />)} />
        <Route path="/screen/:disease" element={guard(<Screening />)} />
        <Route path="/results/:id" element={guard(<Result />)} />
        <Route path="/image" element={guard(<ImageScreening />)} />
        <Route path="/history" element={guard(<History />)} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
