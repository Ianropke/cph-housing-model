import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import { CityProvider } from './context/CityContext.jsx';
import './index.css';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <CityProvider>
      <App />
    </CityProvider>
  </StrictMode>,
);
