import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import AuditLog, Claim, Policy, Rider
from backend.triggers.fraud_engine import FraudEngine, TRIGGER_THRESHOLDS
from backend.triggers.premium_service import PremiumService
from backend.triggers.weather_service import FIXTURE_VERSION, WeatherService, ZONES

router = APIRouter(prefix="/api", tags=["simulation_and_integrations"])
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

EXCLUSIONS_VERSION = "v1.0.0"
EXCLUSIONS = [
    "Health, injury, or accident of any kind",
    "Vehicle damage, repair, or maintenance",
    "Income loss due to personal decision not to work",
    "Disruptions caused by war, armed conflict, or military operations",
    "Pandemic or epidemic declared events",
    "Nuclear events or radiation incidents",
    "Disruptions caused by rider platform violations or account suspension",
    "Pre-existing platform bans or rating-based deactivations",
    "Income loss unrelated to an active parametric trigger",
    "Civil unrest or protests the rider participated in",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read_json(name: str) -> Dict[str, Any]:
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _ensure_rider_and_policy(db: Session, rider_id: str, zone: str, exclusions_acknowledged: bool = True) -> Policy:
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if rider is None:
        rider = Rider(
            id=rider_id,
            name="Demo Rider",
            phone=f"9{uuid4().hex[:9]}",
            delhivery_partner_id=f"DEL-{uuid4().hex[:8].upper()}",
            zone=zone,
            upi_id="demo@okicici",
            avg_daily_earnings=1050.0,
            claim_rate_12wk=0.6,
            fraud_flag_count=0,
            kyc_verified=True,
        )
        db.add(rider)
        db.flush()

    now = _now()
    week_start = now - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=6)
    policy = (
        db.query(Policy)
        .filter(Policy.rider_id == rider_id, Policy.week_start_date >= week_start, Policy.status == "active")
        .first()
    )
    if policy is None:
        premium = PremiumService.predict({"zone": zone, "forecast_features": {}, "rider_features": {}})
        policy = Policy(
            id=f"pol_{uuid4().hex[:10]}",
            rider_id=rider_id,
            week_start_date=week_start,
            week_end_date=week_end,
            base_premium=premium["base_premium"],
            final_premium=premium["final_premium"],
            premium_breakdown=premium["adjustments"],
            coverage_cap=2300.0,
            status="active",
            exclusions_acknowledged_at=now if exclusions_acknowledged else None,
        )
        db.add(policy)
    return policy


class PremiumPredictRequest(BaseModel):
    zone: str = "HSR Layout"
    forecast_features: Dict[str, Any] = Field(default_factory=dict)
    rider_features: Dict[str, Any] = Field(default_factory=dict)
    is_simulated: bool = True


class TriggerSimulateRequest(BaseModel):
    zone: str = "HSR Layout"
    trigger_type: str = "HEAVY_RAIN"
    as_of: Optional[str] = None
    is_simulated: bool = True
    trigger_value: Optional[float] = None
    rider_id: str = "rdr_demo_hsr"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    avg_daily_earnings: float = 1050.0


class PolicyActivateRequest(BaseModel):
    rider_id: str
    zone: str
    exclusions_accepted: bool
    forecast_features: Dict[str, Any] = Field(default_factory=dict)
    rider_features: Dict[str, Any] = Field(default_factory=dict)


@router.get("/exclusions")
def get_exclusions():
    return {"version": EXCLUSIONS_VERSION, "items": EXCLUSIONS}


@router.post("/premium/predict")
def predict_premium(payload: PremiumPredictRequest):
    if payload.zone not in ZONES:
        raise HTTPException(status_code=422, detail={"error": "UNSUPPORTED_ZONE", "message": "Zone is not supported"})
    return PremiumService.predict(payload.model_dump())


@router.get("/weather/current/{zone}")
def get_current_weather(zone: str, is_simulated: bool = Query(False)):
    try:
        return WeatherService.get_current_conditions(zone, is_simulated=is_simulated)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "UNSUPPORTED_ZONE", "message": str(exc)}) from exc


@router.get("/weather/warnings/{zone}")
def get_weather_warnings(zone: str, is_simulated: bool = Query(False)):
    try:
        warnings = WeatherService.get_forecast_warnings(zone, is_simulated=is_simulated)
        return {"zone": zone, "warnings": warnings}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "UNSUPPORTED_ZONE", "message": str(exc)}) from exc


@router.get("/mock/delhivery/{zone}/{date}")
def get_delhivery_metrics(zone: str, date: str):
    data = _read_json("delhivery_cancellations.json")
    record = data.get(zone)
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "ZONE_NOT_FOUND", "message": f"No mock data for zone {zone}"})
    return {
        "zone": zone,
        "date": date,
        "total_banking_orders": int(record.get("total_orders", 0)),
        "cancelled_orders": int(record.get("cancelled_orders", 0)),
        "cancellation_rate_pct": round(float(record.get("cancellation_rate", 0.0)) * 100, 2),
        "note": "Demo fixture",
        "fixture_version": FIXTURE_VERSION,
    }


@router.get("/mock/branches/{zone}")
def get_banking_metrics(zone: str):
    data = _read_json("bank_branches.json")
    record = data.get(zone)
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "ZONE_NOT_FOUND", "message": f"No mock data for zone {zone}"})
    closure_rate_pct = round(float(record.get("closure_rate", 0.0)) * 100, 2)
    return {
        "zone": zone,
        "total_branches": int(record.get("total_branches", 0)),
        "closed_branches": int(record.get("closed_branches", 0)),
        "closure_rate_pct": closure_rate_pct,
        "threshold_pct": 60.0,
        "trigger_breached": closure_rate_pct >= 60.0,
        "fixture_version": FIXTURE_VERSION,
    }


@router.post("/policies/activate")
def activate_policy(payload: PolicyActivateRequest, db: Session = Depends(get_db)):
    if payload.zone not in ZONES:
        raise HTTPException(status_code=422, detail={"error": "UNSUPPORTED_ZONE", "message": "Unsupported zone"})
    if not payload.exclusions_accepted:
        raise HTTPException(
            status_code=422,
            detail={"error": "EXCLUSIONS_NOT_ACKNOWLEDGED", "message": "Policy activation requires exclusions acceptance"},
        )

    policy = _ensure_rider_and_policy(db, rider_id=payload.rider_id, zone=payload.zone, exclusions_acknowledged=True)
    premium = PremiumService.predict(
        {
            "zone": payload.zone,
            "forecast_features": payload.forecast_features,
            "rider_features": payload.rider_features,
            "is_simulated": True,
        }
    )

    policy.base_premium = premium["base_premium"]
    policy.final_premium = premium["final_premium"]
    policy.premium_breakdown = premium["adjustments"]
    policy.exclusions_acknowledged_at = _now()
    policy.status = "active"

    db.add(
        AuditLog(
            entity_type="Policy",
            entity_id=policy.id,
            action="POLICY_ACTIVATED",
            metadata_json={"rider_id": payload.rider_id, "zone": payload.zone, "exclusions_version": EXCLUSIONS_VERSION},
        )
    )
    db.commit()
    db.refresh(policy)

    return {
        "policy_id": policy.id,
        "rider_id": payload.rider_id,
        "zone": payload.zone,
        "status": policy.status,
        "base_premium": policy.base_premium,
        "final_premium": policy.final_premium,
        "premium_breakdown": policy.premium_breakdown,
        "exclusions_version": EXCLUSIONS_VERSION,
        "exclusions_acknowledged_at": policy.exclusions_acknowledged_at.isoformat() if policy.exclusions_acknowledged_at else None,
    }


@router.post("/triggers/simulate")
def simulate_trigger(payload: TriggerSimulateRequest, db: Session = Depends(get_db)):
    trigger_type = payload.trigger_type.upper()
    if trigger_type not in TRIGGER_THRESHOLDS:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "UNSUPPORTED_TRIGGER",
                "message": "trigger_type must be one of HEAVY_RAIN, EXTREME_HEAT, SEVERE_AQI, BRANCH_CLOSURE, DELHIVERY_ADVISORY",
            },
        )

    if payload.zone not in ZONES:
        raise HTTPException(status_code=422, detail={"error": "UNSUPPORTED_ZONE", "message": "Unsupported zone"})

    weather = WeatherService.get_current_conditions(payload.zone, is_simulated=payload.is_simulated)
    trigger_view = weather["trigger_view"]

    derived_value = payload.trigger_value
    if derived_value is None:
        if trigger_type == "HEAVY_RAIN":
            derived_value = float(trigger_view["heavy_rain"]["value"])
        elif trigger_type == "EXTREME_HEAT":
            derived_value = float(trigger_view["extreme_heat"]["value"])
        elif trigger_type == "SEVERE_AQI":
            derived_value = float(trigger_view["severe_aqi"]["value"])
        elif trigger_type == "BRANCH_CLOSURE":
            branch = get_banking_metrics(payload.zone)
            derived_value = float(branch["closure_rate_pct"])
        else:
            delhivery = get_delhivery_metrics(payload.zone, _now().date().isoformat())
            derived_value = float(delhivery["cancellation_rate_pct"])

    policy = _ensure_rider_and_policy(db, rider_id=payload.rider_id, zone=payload.zone)

    result = FraudEngine.evaluate_claim(
        zone=payload.zone,
        trigger_type=trigger_type,
        trigger_value=float(derived_value),
        rider_id=payload.rider_id,
        avg_daily_earnings=payload.avg_daily_earnings,
        is_simulated=payload.is_simulated,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    claim = Claim(
        id=result["claim_id"],
        policy_id=policy.id,
        rider_id=payload.rider_id,
        zone=payload.zone,
        trigger_type=trigger_type,
        trigger_value=float(derived_value),
        trigger_threshold=float(result["trigger_event"]["threshold"]),
        is_simulated=payload.is_simulated,
        fraud_check_passed=result["fraud_check_passed"],
        fraud_layers=result["fraud_layers"],
        payout_amount=float(result["recommended_payout"]),
        payout_status="credited" if result["recommended_payout"] > 0 else "rejected",
        payout_initiated_at=_now() if result["recommended_payout"] > 0 else None,
        delhivery_cancellation_rate=next(
            (
                layer["evidence"].get("cancellation_rate_pct", 0.0)
                for layer in result["fraud_layers"]
                if layer["layer"] == "L3_DELHIVERY_CROSS_REF"
            ),
            0.0,
        ),
    )
    db.add(claim)
    db.add(
        AuditLog(
            entity_type="Simulation",
            entity_id=result["claim_id"],
            action="TRIGGER_SIMULATION_EXECUTED",
            metadata_json={"zone": payload.zone, "trigger_type": trigger_type, "is_simulated": payload.is_simulated},
        )
    )
    db.commit()

    return {
        "simulation_id": f"sim_{uuid4().hex[:8]}",
        "zone": payload.zone,
        "trigger_type": trigger_type,
        "trigger_event": result["trigger_event"],
        "riders_evaluated": 1,
        "claims_preview": [
            {
                "rider_id": payload.rider_id,
                "fraud_check_passed": result["fraud_check_passed"],
                "fraud_layers": result["fraud_layers"],
                "recommended_payout": result["recommended_payout"],
                "currency": result["currency"],
                "claim_id": result["claim_id"],
            }
        ],
        "fixture_version": FIXTURE_VERSION if payload.is_simulated else None,
    }


@router.get("/policies/{rider_id}/current")
def get_current_policy(rider_id: str, db: Session = Depends(get_db)):
    policy = (
        db.query(Policy)
        .filter(Policy.rider_id == rider_id, Policy.status == "active")
        .order_by(Policy.created_at.desc())
        .first()
    )
    if policy is None:
        raise HTTPException(status_code=404, detail={"error": "POLICY_NOT_FOUND", "message": "No active policy"})
    return {
        "policy_id": policy.id,
        "rider_id": rider_id,
        "week_start_date": policy.week_start_date.isoformat() if policy.week_start_date else None,
        "week_end_date": policy.week_end_date.isoformat() if policy.week_end_date else None,
        "base_premium": policy.base_premium,
        "final_premium": policy.final_premium,
        "premium_breakdown": policy.premium_breakdown,
        "coverage_cap": policy.coverage_cap,
        "status": policy.status,
        "exclusions_version": EXCLUSIONS_VERSION,
        "exclusions_acknowledged_at": policy.exclusions_acknowledged_at.isoformat() if policy.exclusions_acknowledged_at else None,
    }


@router.get("/claims/{rider_id}")
def get_claims_for_rider(rider_id: str, db: Session = Depends(get_db)):
    rows = db.query(Claim).filter(Claim.rider_id == rider_id).order_by(Claim.created_at.desc()).all()
    return {
        "rider_id": rider_id,
        "count": len(rows),
        "claims": [
            {
                "claim_id": row.id,
                "trigger_type": row.trigger_type,
                "trigger_value": row.trigger_value,
                "trigger_threshold": row.trigger_threshold,
                "fraud_check_passed": row.fraud_check_passed,
                "fraud_layers": row.fraud_layers,
                "payout_amount": row.payout_amount,
                "payout_status": row.payout_status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "is_simulated": row.is_simulated,
            }
            for row in rows
        ],
    }
