"""
ML model API routes.
"""
from fastapi import APIRouter, HTTPException

from app.ml.predict import get_predictor
from app.schemas.schemas import PredictionRequest, PredictionResponse, ModelInfoResponse

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    """Run fraud prediction on transaction data."""
    predictor = get_predictor()
    if not predictor.loaded:
        raise HTTPException(status_code=503, detail="ML model not loaded. Please train the model first.")

    tx_data = {
        "amount": req.amount,
        "account_id": req.account_id,
        "device_id": req.device_fingerprint,
        "ip_address": req.ip_address,
        "merchant_id": req.merchant_code,
        "failed_attempts": req.failed_attempts,
        "is_new_device": req.is_new_device,
        "is_new_ip": req.is_new_ip,
        "transaction_frequency": 0,
        "account_average_amount": req.amount,
        "time_since_last_transaction": 24.0,
        "merchant_frequency": 0,
        "device_usage_count": 1,
        "ip_usage_count": 1,
    }

    try:
        result = predictor.predict(tx_data)
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/model-info", response_model=ModelInfoResponse)
def get_model_info():
    """Get current model information and metrics."""
    predictor = get_predictor()
    info = predictor.get_model_info()
    return ModelInfoResponse(**info)
