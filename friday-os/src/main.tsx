import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// StrictMode removed: it double-invokes useEffect cleanup in dev,
// which destroys the LiveKit Room object before the second mount can use it.
createRoot(document.getElementById('root')!).render(<App />)
