from typing import Optional, Dict, Any, List
from schemas.sensor import SensorReading


def generate_environmental_assessment(
    crop: str,
    disease: str,
    is_healthy: bool,
    sensor_reading: Optional[SensorReading]
) -> Dict[str, Any]:
    """
    Combines leaf image disease prediction with valid sensor telemetry.
    If sensor_reading is None or empty, returns empty sensor insights,
    preserving the existing image-only advisory without alteration.
    """
    if not sensor_reading:
        return {
            "environmental_assessment": None,
            "sensor_alerts": [],
            "sensor_telemetry_used": None,
            "data_source": "none"
        }

    alerts: List[str] = []
    assessment_notes: List[str] = []
    disease_lower = (disease or "").lower()

    # 1. Temperature Assessment
    temp = sensor_reading.temp_avg or sensor_reading.temperature1
    if temp is not None:
        if temp > 35.0:
            alerts.append(f"High Ambient Temperature Warning ({temp}°): Elevated heat may cause foliar heat stress and rapid water loss.")
            assessment_notes.append(f"Temperature is recorded at {temp}, which exceeds standard cool-canopy conditions.")
        elif temp < 15.0 and "late blight" in disease_lower:
            alerts.append(f"Cool Canopy Warning ({temp}°): Late blight (Phytophthora) spreads rapidly in cool, moist environments.")
            assessment_notes.append(f"Low temperature ({temp}) combined with foliar moisture creates high risk for late blight pathogen sporulation.")

    # 2. Humidity Assessment
    hum = sensor_reading.humidity_avg or sensor_reading.humidity1
    if hum is not None:
        if hum >= 80.0:
            alerts.append(f"Critical Humidity Alert ({hum}%): Relative humidity > 80% creates condensation on leaf surfaces, accelerating spore germination.")
            if "blight" in disease_lower or "spot" in disease_lower:
                assessment_notes.append(f"High relative humidity ({hum}%) directly exacerbates {disease} transmission. Increase polyhouse side-ventilation immediately.")
            elif is_healthy:
                assessment_notes.append(f"High relative humidity ({hum}%) detected. While current foliage is healthy, inspect leaf undersides for condensation to prevent fungal onset.")
        elif hum < 30.0:
            alerts.append(f"Low Relative Humidity ({hum}%): Extremely dry air may lead to foliar desiccation or spider mite pressure.")

    # 3. Water & Nutrient Solution Assessment (pH, EC, TDS, Salinity)
    if sensor_reading.ph is not None:
        if sensor_reading.ph < 5.5:
            alerts.append(f"Irrigation Solution Acidic (pH {sensor_reading.ph}): Low pH can induce micronutrient toxicity and weaken plant cell walls.")
        elif sensor_reading.ph > 7.5:
            alerts.append(f"Irrigation Solution Alkaline (pH {sensor_reading.ph}): High pH inhibits calcium and iron uptake, predisposing solanaceous crops to root stress.")

    if sensor_reading.ec is not None and sensor_reading.ec > 2500.0:
        alerts.append(f"Elevated Solution EC ({sensor_reading.ec} µS/cm): High electrical conductivity indicates salt accumulation; flush root zone with clean water.")

    # 4. Light / LDR Assessment
    ldr = sensor_reading.ldr1
    if ldr is not None and hum is not None and hum > 75.0 and ldr < 2000.0:
        alerts.append("Low Light & High Humidity: Extended leaf wetness duration likely due to minimal solar radiation. Ensure active ventilation.")

    # Construct synthesized summary text
    if assessment_notes:
        summary_text = " ".join(assessment_notes)
    elif alerts:
        summary_text = f"Environmental telemetry analyzed: {len(alerts)} microclimate factor(s) flagged for attention alongside foliar diagnosis."
    else:
        summary_text = "Microclimate parameters are currently within normal baseline ranges for protected cultivation."

    source = "demo_sample" if sensor_reading.is_demo else "live_gateway"

    telemetry_summary = {
        "device_id": sensor_reading.device_id,
        "timestamp": sensor_reading.timestamp,
        "temp_avg": sensor_reading.temp_avg,
        "humidity_avg": sensor_reading.humidity_avg,
        "ph": sensor_reading.ph,
        "tds": sensor_reading.tds,
        "ec": sensor_reading.ec,
        "salinity": sensor_reading.salinity,
        "ldr1": sensor_reading.ldr1,
        "is_stale": sensor_reading.is_stale,
        "is_demo": sensor_reading.is_demo
    }

    return {
        "environmental_assessment": summary_text,
        "sensor_alerts": alerts,
        "sensor_telemetry_used": telemetry_summary,
        "data_source": source
    }


def enrich_advisory(
    base_advisory: Dict[str, Any],
    crop: str,
    disease: str,
    is_healthy: bool,
    sensor_reading: Optional[SensorReading]
) -> Dict[str, Any]:
    """
    Preserves all original fields of base_advisory (description, symptoms,
    preventive_measures, management) and enriches it with the combined sensor advisory.
    """
    enriched = dict(base_advisory)
    combined = generate_environmental_assessment(crop, disease, is_healthy, sensor_reading)

    enriched["environmental_assessment"] = combined["environmental_assessment"]
    enriched["sensor_alerts"] = combined["sensor_alerts"]
    enriched["sensor_telemetry_used"] = combined["sensor_telemetry_used"]
    enriched["data_source"] = combined["data_source"]

    # Append any specific sensor alerts to management recommendations if applicable
    if combined["sensor_alerts"]:
        existing_mgmt = list(enriched.get("management", []))
        for alert in combined["sensor_alerts"]:
            recom = f"[Environmental Advisory] {alert}"
            if recom not in existing_mgmt:
                existing_mgmt.append(recom)
        enriched["management"] = existing_mgmt

    return enriched
