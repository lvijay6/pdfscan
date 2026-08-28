from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import uuid
import base64

from backend.app.services.image_processor import ImageProcessor
from backend.app.services.ocr_service import OCREngine
from backend.app.services.scan_cache import scan_cache

router = APIRouter(prefix="/api/v1/scan", tags=["Scan & Preview"])

class CropTransformRequest(BaseModel):
    session_id: str
    page_index: int
    pts: List[List[int]]

class EditPageRequest(BaseModel):
    session_id: str
    page_index: int
    rotation: Optional[int] = 0
    brightness: Optional[float] = 1.0
    contrast: Optional[float] = 1.0
    filter_name: Optional[str] = "original"

class ReorderPagesRequest(BaseModel):
    session_id: str
    new_order: List[int]

class SplitPagesRequest(BaseModel):
    session_id: str
    split_indices: List[int]

class MergeSessionsRequest(BaseModel):
    session_ids: List[str]

@router.post("/detect-edges")
async def detect_edges(file: UploadFile = File(...)):
    contents = await file.read()
    img = ImageProcessor.load_image_from_bytes(contents)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    pts = ImageProcessor.detect_edges(img)
    img_b64 = base64.b64encode(contents).decode("utf-8")
    return {
        "width": img.shape[1],
        "height": img.shape[0],
        "crop_pts": pts,
        "image_b64": f"data:image/png;base64,{img_b64}"
    }

@router.post("/process-page")
async def process_page(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    filter_name: Optional[str] = Form("original"),
    brightness: Optional[float] = Form(1.0),
    contrast: Optional[float] = Form(1.0),
    rotation: Optional[int] = Form(0)
):
    contents = await file.read()
    img = ImageProcessor.load_image_from_bytes(contents)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    if rotation:
        img = ImageProcessor.rotate_image(img, rotation)

    pts = ImageProcessor.detect_edges(img)
    warped = ImageProcessor.four_point_transform(img, pts)
    filtered = ImageProcessor.apply_filter(warped, filter_name)
    adjusted = ImageProcessor.adjust_brightness_contrast(filtered, brightness, contrast)

    ocr_text = OCREngine.extract_text(adjusted)
    ocr_data = OCREngine.extract_detailed_data(adjusted)
    doc_type = OCREngine.classify_document(ocr_text)

    img_bytes = ImageProcessor.to_bytes(adjusted)
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    page_data = {
        "page_id": str(uuid.uuid4()),
        "image_b64": f"data:image/png;base64,{img_b64}",
        "raw_image_b64": f"data:image/png;base64,{base64.b64encode(contents).decode('utf-8')}",
        "pts": pts,
        "rotation": rotation,
        "brightness": brightness,
        "contrast": contrast,
        "filter_name": filter_name,
        "ocr_text": ocr_text,
        "ocr_boxes": ocr_data.get("words", []),
        "doc_type": doc_type
    }

    if not session_id:
        session_id = str(uuid.uuid4())
        pages = [page_data]
    else:
        pages = scan_cache.get_session(session_id)
        pages.append(page_data)

    scan_cache.save_session(session_id, pages)

    return {
        "session_id": session_id,
        "page": page_data,
        "total_pages": len(pages)
    }

@router.get("/preview/{session_id}")
def get_session_preview(session_id: str):
    pages = scan_cache.get_session(session_id)
    if not pages:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {
        "session_id": session_id,
        "pages": pages
    }

@router.post("/crop")
def crop_page(req: CropTransformRequest):
    pages = scan_cache.get_session(req.session_id)
    if not pages or req.page_index >= len(pages):
        raise HTTPException(status_code=404, detail="Session or page not found")

    raw_b64 = pages[req.page_index]["raw_image_b64"].split(",")[-1]
    raw_bytes = base64.b64decode(raw_b64)
    img = ImageProcessor.load_image_from_bytes(raw_bytes)

    if pages[req.page_index].get("rotation"):
        img = ImageProcessor.rotate_image(img, pages[req.page_index]["rotation"])

    warped = ImageProcessor.four_point_transform(img, req.pts)
    filtered = ImageProcessor.apply_filter(warped, pages[req.page_index].get("filter_name", "original"))
    adjusted = ImageProcessor.adjust_brightness_contrast(filtered, pages[req.page_index].get("brightness", 1.0), pages[req.page_index].get("contrast", 1.0))

    ocr_text = OCREngine.extract_text(adjusted)
    ocr_data = OCREngine.extract_detailed_data(adjusted)

    img_bytes = ImageProcessor.to_bytes(adjusted)
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    pages[req.page_index]["pts"] = req.pts
    pages[req.page_index]["image_b64"] = f"data:image/png;base64,{img_b64}"
    pages[req.page_index]["ocr_text"] = ocr_text
    pages[req.page_index]["ocr_boxes"] = ocr_data.get("words", [])

    scan_cache.save_session(req.session_id, pages)
    return {"session_id": req.session_id, "page": pages[req.page_index]}

@router.post("/edit-page")
def edit_page(req: EditPageRequest):
    pages = scan_cache.get_session(req.session_id)
    if not pages or req.page_index >= len(pages):
        raise HTTPException(status_code=404, detail="Session or page not found")

    p = pages[req.page_index]
    raw_bytes = base64.b64decode(p["raw_image_b64"].split(",")[-1])
    img = ImageProcessor.load_image_from_bytes(raw_bytes)

    img = ImageProcessor.rotate_image(img, req.rotation)
    pts = p.get("pts", ImageProcessor.detect_edges(img))
    warped = ImageProcessor.four_point_transform(img, pts)
    filtered = ImageProcessor.apply_filter(warped, req.filter_name)
    adjusted = ImageProcessor.adjust_brightness_contrast(filtered, req.brightness, req.contrast)

    img_bytes = ImageProcessor.to_bytes(adjusted)
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    p["rotation"] = req.rotation
    p["brightness"] = req.brightness
    p["contrast"] = req.contrast
    p["filter_name"] = req.filter_name
    p["image_b64"] = f"data:image/png;base64,{img_b64}"

    scan_cache.save_session(req.session_id, pages)
    return {"session_id": req.session_id, "page": p}

@router.delete("/page/{session_id}/{page_index}")
def delete_page(session_id: str, page_index: int):
    pages = scan_cache.get_session(session_id)
    if not pages or page_index >= len(pages):
        raise HTTPException(status_code=404, detail="Session or page not found")

    pages.pop(page_index)
    scan_cache.save_session(session_id, pages)
    return {"session_id": session_id, "remaining_pages": len(pages)}

@router.post("/reorder")
def reorder_pages(req: ReorderPagesRequest):
    pages = scan_cache.get_session(req.session_id)
    if not pages:
        raise HTTPException(status_code=404, detail="Session not found")

    reordered = [pages[i] for i in req.new_order if 0 <= i < len(pages)]
    scan_cache.save_session(req.session_id, reordered)
    return {"session_id": req.session_id, "total_pages": len(reordered)}

@router.post("/split")
def split_session(req: SplitPagesRequest):
    pages = scan_cache.get_session(req.session_id)
    if not pages:
        raise HTTPException(status_code=404, detail="Session not found")

    split_indices = sorted(list(set([0] + req.split_indices)))
    new_sessions = []

    for i in range(len(split_indices)):
        start = split_indices[i]
        end = split_indices[i+1] if i + 1 < len(split_indices) else len(pages)
        sub_pages = pages[start:end]
        if sub_pages:
            new_id = str(uuid.uuid4())
            scan_cache.save_session(new_id, sub_pages)
            new_sessions.append({"session_id": new_id, "page_count": len(sub_pages)})

    return {"new_sessions": new_sessions}

@router.post("/merge")
def merge_sessions(req: MergeSessionsRequest):
    merged_pages = []
    for sid in req.session_ids:
        p = scan_cache.get_session(sid)
        merged_pages.extend(p)

    new_id = str(uuid.uuid4())
    scan_cache.save_session(new_id, merged_pages)
    return {"session_id": new_id, "total_pages": len(merged_pages)}
