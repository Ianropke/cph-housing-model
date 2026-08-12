export const REQUIRED_SEGMENTS = [
  'copenhagen_apartments',
  'copenhagen_houses',
  'frederiksberg_apartments',
];

const REQUIRED_HORIZONS = ['6m', '12m', '24m'];
const REQUIRED_MODES = ['yoy_original', 'yoy_expanded', 'structural_3y', 'structural_5y'];

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function isDate(value) {
  return typeof value === 'string' && Number.isFinite(new Date(value).getTime());
}

export function validatePipelinePayload(payload, { now = Date.now(), maxAgeHours = 48 } = {}) {
  const errors = [];
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return { valid: false, errors: ['Payload er ikke et JSON-objekt'] };
  }

  if (payload.schema_version !== 1) errors.push('Payloadens schema-version er ikke understøttet');
  if (!isDate(payload.generated_at)) {
    errors.push('Payload mangler et gyldigt genereringstidspunkt');
  } else {
    const ageHours = (now - new Date(payload.generated_at).getTime()) / 3600000;
    if (ageHours < -1) errors.push('Payloadens genereringstidspunkt ligger i fremtiden');
    if (ageHours > maxAgeHours) errors.push(`Payloaden er for gammel (${ageHours.toFixed(1)} timer)`);
  }

  const marketStatus = payload.market_data_status;
  if (!marketStatus || typeof marketStatus !== 'object') {
    errors.push('Live markedsdatastatus mangler');
  } else {
    if (marketStatus.status !== 'live') errors.push('Markedsdata er ikke verificeret som live');
    if (!isDate(marketStatus.generated_at)) errors.push('Markedsdatastatus mangler tidspunkt');
    if (!marketStatus.sources || typeof marketStatus.sources !== 'object') errors.push('Markedsdatakilder mangler');
  }

  const dstSegments = payload.dst_data?.segments;
  const forecasts = payload.forecasts;
  const earlyWarnings = payload.early_warnings;
  if (!dstSegments || typeof dstSegments !== 'object') errors.push('DST-segmenter mangler');
  if (!forecasts || typeof forecasts !== 'object') errors.push('Forecasts mangler');
  if (!earlyWarnings || typeof earlyWarnings !== 'object') errors.push('Early-warning-data mangler');

  for (const segment of REQUIRED_SEGMENTS) {
    const dst = dstSegments?.[segment];
    if (!dst || typeof dst !== 'object') {
      errors.push(`${segment}: DST-data mangler`);
      continue;
    }

    if (typeof dst.latest_period !== 'string' || !dst.latest_period) errors.push(`${segment}: seneste DST-periode mangler`);
    if (!isFiniteNumber(dst.latest_value)) errors.push(`${segment}: seneste DST-værdi er ugyldig`);
    if (!dst.series || typeof dst.series !== 'object' || !Object.keys(dst.series).length) errors.push(`${segment}: DST-serie mangler`);
    if (dst.latest_period && !Object.prototype.hasOwnProperty.call(dst.series || {}, dst.latest_period)) {
      errors.push(`${segment}: seneste periode findes ikke i DST-serien`);
    }

    const forecast = forecasts?.[segment];
    if (!forecast || typeof forecast !== 'object') {
      errors.push(`${segment}: forecast mangler`);
    } else {
      if (forecast.current_period !== dst.latest_period) errors.push(`${segment}: forecast og DST har forskellige perioder`);
      if (!isFiniteNumber(forecast.current_index)) errors.push(`${segment}: forecastets aktuelle indeks er ugyldigt`);
      if (isFiniteNumber(dst.latest_value) && isFiniteNumber(forecast.current_index)
        && Math.abs(forecast.current_index - dst.latest_value) > 1e-9) {
        errors.push(`${segment}: forecast og DST har forskellige aktuelle indeks`);
      }
      for (const horizon of REQUIRED_HORIZONS) {
        if (!forecast.horizons?.[horizon]?.ensemble) errors.push(`${segment}: forecast ${horizon} mangler ensemble`);
      }
    }

    const ewi = earlyWarnings?.[segment];
    if (!ewi || typeof ewi !== 'object') {
      errors.push(`${segment}: early-warning-data mangler`);
    } else {
      if (!isFiniteNumber(ewi.composite_score)) errors.push(`${segment}: EWI-score er ugyldig`);
      for (const mode of REQUIRED_MODES) {
        if (!Array.isArray(ewi.modes?.[mode]?.earlyWarningIndicators)) errors.push(`${segment}: EWI-mode ${mode} mangler`);
      }
    }
  }

  return { valid: errors.length === 0, errors };
}
