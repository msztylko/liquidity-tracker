import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Overview from './pages/Overview'
import Metrics from './pages/Metrics'
import Analysis from './pages/Analysis'

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route index element={<Navigate to="/overview" replace />} />
                    <Route path="overview" element={<Overview />} />
                    <Route path="metrics" element={<Metrics />} />
                    <Route path="analysis" element={<Analysis />} />
                </Route>
            </Routes>
        </Router>
    )
}

export default App
