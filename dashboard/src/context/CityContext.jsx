import React, { createContext, useContext, useState, useEffect } from 'react';

const CityContext = createContext();

export function CityProvider({ children }) {
  const [pipelineData, setPipelineData] = useState(null);
  const [activeCity, setActiveCity] = useState('copenhagen');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/data/latest_pipeline.json?t=' + new Date().getTime())
      .then(res => res.json())
      .then(data => {
        setPipelineData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load data', err);
        setLoading(false);
      });
  }, []);

  const value = {
    pipelineData,
    activeCity,
    setActiveCity,
    loading
  };

  return <CityContext.Provider value={value}>{children}</CityContext.Provider>;
}

export function useCity() {
  return useContext(CityContext);
}
