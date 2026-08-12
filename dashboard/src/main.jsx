import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import { CityProvider } from './context/CityProvider.jsx';
import { Analytics } from '@vercel/analytics/react';
import './index.css';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <CityProvider>
      <Analytics />
      <App />
    </CityProvider>
  </StrictMode>,
);
