from fastapi import FastAPI
from .schemas import ComplianceRequest, ComplianceResult
from .eval.compliance import ComplianceEvaluator
from .api.routes_publish import router as publish_router
from .api.routes_track import router as track_router
from .api.routes_ingest import router as ingest_router
from .api.routes_ops import router as ops_router

app = FastAPI(title="Content Compliance Engine")
app.include_router(publish_router)
app.include_router(track_router)
app.include_router(ingest_router)
app.include_router(ops_router)
evaluator = ComplianceEvaluator()

@app.post("/check", response_model=ComplianceResult)
async def check_compliance(request: ComplianceRequest):
    return evaluator.evaluate(request)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
