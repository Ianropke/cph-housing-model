from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scenario_weights_are_labelled_as_model_weights():
    text = (ROOT / "dashboard/src/components/ForecastEnsemblePanel.jsx").read_text(encoding="utf-8")
    assert "modelvægte, ikke estimerede sandsynligheder" in text
    assert "P10–P90-båndet" in text
    assert "Hvert scenarie har en sandsynlighedsvægt" not in text
    assert "Monte Carlo 90% konfidensinterval" not in text


def test_downside_barometer_labels_simulation_as_sensitivity_output():
    text = (ROOT / "dashboard/src/components/RiskBarometer.jsx").read_text(encoding="utf-8")
    assert "simulationsfrekvens/sensitivitetsmåling" in text
    assert "ikke en procentchance" in text
    assert "Monte Carlo-nedrisiko måler sandsynligheden" not in text
