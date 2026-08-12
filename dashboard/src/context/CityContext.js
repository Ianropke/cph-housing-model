import { createContext, useContext } from 'react';

export const CityContext = createContext(null);

export function useCity() {
  const context = useContext(CityContext);
  if (!context) throw new Error('useCity skal bruges inden for CityProvider');
  return context;
}
