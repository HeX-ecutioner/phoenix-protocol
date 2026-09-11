import hashlib

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.db import get_connection, init_db
from app.models import ScanRequest, UploadObject
from app.parser import ParserException
from app.repository import ScanRepository
from app.service import run_scan

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    init_db(conn)
    conn.close()
    yield


app = FastAPI(title="Phoenix Protocol Analysis API", lifespan=lifespan)


def get_db():
    conn = get_connection()
    try:
        yield ScanRepository(conn)
    finally:
        conn.close()


@app.post("/scan", status_code=201)
async def upload_and_scan(
    file: UploadFile = File(...), db: ScanRepository = Depends(get_db)
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty input")

    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB limit
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    sha256 = hashlib.sha256(content).hexdigest()

    upload_obj = UploadObject(
        original_filename=file.filename or "unknown",
        content=content,
        content_type=file.content_type,
        size_bytes=len(content),
        sha256=sha256,
        format_hint=None,
    )

    request = ScanRequest(upload=upload_obj)

    try:
        result = run_scan(request, db)
    except ParserException as e:
        raise HTTPException(
            status_code=422, detail=f"Unrecoverable parser error: {str(e)}"
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected infrastructure failure")

    if result.status == "failed":
        return JSONResponse(status_code=422, content=jsonable_encoder(result))

    return result


@app.get("/scans/{scan_id}")
async def get_scan_result(scan_id: str, db: ScanRepository = Depends(get_db)):
    result = db.get_scan(scan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result
