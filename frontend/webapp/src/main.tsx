/**
 * Main entry point for FrozenBot WebApp
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/index.css'

// Initialize React app
const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Failed to find root element. Make sure there is a div with id="root" in your HTML.')
}

const root = ReactDOM.createRoot(rootElement)
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)