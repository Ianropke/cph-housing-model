import { useEffect, useState } from 'react';
import { CityContext } from './CityContext';
import { validatePipelinePayload } from '../data/pipelineSchema';

export function CityProvider({ children }) {
  const [pipelineData, setPipelineData] = useState(null);
  const [activeCity, setActiveCity] = useState('copenhagen');
  const [dataStatus, setDataStatus] = useState('loading');
  const [dataErrors, setDataErrors] = useState([]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPayload() {
      try {
        const response = await fetch(`/data/latest_pipeline.json?t=${Date.now()}`, {
          signal: controller.signal,
          cache: 'no-store',
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        const validation = validatePipelinePayload(payload);
        if (!validation.valid) {
          setPipelineData(null);
          setDataErrors(validation.errors);
          setDataStatus(validation.errors.some((error) => error.includes('gammel')) ? 'stale' : 'invalid');
          return;
        }
        setPipelineData(payload);
        setDataErrors([]);
        setDataStatus('live');
      } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('Dashboard payload kunne ikke indlæses', error);
        setPipelineData(null);
        setDataErrors(['Dashboardets seneste datagrundlag kunne ikke indlæses']);
        setDataStatus('unavailable');
      }
    }

    loadPayload();
    return () => controller.abort();
  }, []);

  return (
    <CityContext.Provider value={{
      pipelineData,
      activeCity,
      setActiveCity,
      loading: dataStatus === 'loading',
      dataStatus,
      dataErrors,
    }}>
      {children}
    </CityContext.Provider>
  );
}
