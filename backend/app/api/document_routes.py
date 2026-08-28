from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import os
import uuid
import base64
import io

from backend.app.core.database import get_db
from backend.app.models.schema import Document, ScanPage, AuditLog
from backend.app.services.scan_cache import scan_cache
from backend.app.services.image_processor import ImageProcessor
from backend.app.services.pdf_engine import PDFEngine

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

class SaveDocumentRequest(BaseModel):
    user_id: str
    session_id: str
    name: str
    document_type: Optional[str] = "General"

class ExportDocumentRequest(BaseModel):
    format: str
    password: Optional[str] = None
    compress: Optional[bool] = False

@router.post("/save")
def save_document(req: SaveDocumentRequest, db: Session = Depends(get_db)):
    pages = scan_cache.get_session(req.session_id)
    if not pages:
        raise HTTPException(status_code=404, detail="Scan session not found or expired")

    doc_id = str(uuid.uuid4())
    doc_dir = os.path.join(STORAGE_DIR, doc_id)
    os.makedirs(doc_dir, exist_ok=True)

    img_list = []
    ocr_texts = []
    page_records = []

    for idx, p in enumerate(pages):
        page_id = str(uuid.uuid4())
        img_bytes = base64.b64decode(p["image_b64"].split(",")[-1])
        img = ImageProcessor.load_image_from_bytes(img_bytes)
        img_list.append(img)
        ocr_texts.append(p.get("ocr_text", ""))

        page_img_path = os.path.join(doc_dir, f"page_{idx+1}.png")
        with open(page_img_path, "wb") as f:
            f.write(img_bytes)

        page_rec = ScanPage(
            id=page_id,
            document_id=doc_id,
            page_no=idx + 1,
            image_path=page_img_path,
            ocr_text=p.get("ocr_text", ""),
            ocr_boxes=p.get("ocr_boxes", [])
        )
        page_records.append(page_rec)

    pdf_bytes = PDFEngine.images_to_pdf(img_list)
    pdf_path = os.path.join(doc_dir, "document.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    doc_record = Document(
        id=doc_id,
        user_id=req.user_id,
        name=req.name,
        file_path=pdf_path,
        file_type="pdf",
        document_type=req.document_type or pages[0].get("doc_type", "General"),
        page_count=len(pages),
        ocr_status="COMPLETED"
    )

    db.add(doc_record)
    for pr in page_records:
        db.add(pr)
    db.add(AuditLog(user_id=req.user_id, action=f"DOCUMENT_SAVED: {req.name}"))
    db.commit()

    scan_cache.delete_session(req.session_id)

    return {
        "document_id": doc_id,
        "name": req.name,
        "page_count": len(pages),
        "document_type": doc_record.document_type,
        "message": "Document saved successfully"
    }

@router.get("/list/{user_id}")
def list_documents(user_id: str, search: Optional[str] = None, document_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Document).filter(Document.user_id == user_id)
    if document_type and document_type != "All":
        query = query.filter(Document.document_type == document_type)

    docs = query.order_by(Document.created_at.desc()).all()
    results = []

    for d in docs:
        pages = db.query(ScanPage).filter(ScanPage.document_id == d.id).order_by(ScanPage.page_no).all()
        full_ocr = " ".join([p.ocr_text or "" for p in pages])

        if search and search.strip():
            st = search.strip().lower()
            if st not in d.name.lower() and st not in full_ocr.lower():
                continue

        results.append({
            "id": d.id,
            "name": d.name,
            "document_type": d.document_type,
            "page_count": d.page_count,
            "created_at": d.created_at.isoformat(),
            "is_password_protected": d.is_password_protected,
            "ocr_preview": full_ocr[:150] + "..." if len(full_ocr) > 150 else full_ocr
        })

    return {"documents": results}

@router.get("/detail/{doc_id}")
def get_document_detail(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = db.query(ScanPage).filter(ScanPage.document_id == doc.id).order_by(ScanPage.page_no).all()
    page_details = []

    for p in pages:
        img_b64 = ""
        if os.path.exists(p.image_path):
            with open(p.image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

        page_details.append({
            "id": p.id,
            "page_no": p.page_no,
            "ocr_text": p.ocr_text,
            "ocr_boxes": p.ocr_boxes,
            "image_b64": f"data:image/png;base64,{img_b64}"
        })

    return {
        "id": doc.id,
        "name": doc.name,
        "document_type": doc.document_type,
        "page_count": doc.page_count,
        "created_at": doc.created_at.isoformat(),
        "pages": page_details
    }

@router.post("/export/{doc_id}")
def export_document(doc_id: str, req: ExportDocumentRequest, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = db.query(ScanPage).filter(ScanPage.document_id == doc.id).order_by(ScanPage.page_no).all()
    img_list = []
    ocr_texts = []

    for p in pages:
        if os.path.exists(p.image_path):
            with open(p.image_path, "rb") as f:
                img_bytes = f.read()
            img = ImageProcessor.load_image_from_bytes(img_bytes)
            img_list.append(img)
            ocr_texts.append(p.ocr_text or "")

    fmt = req.format.lower()
    if fmt == "searchable_pdf":
        out_bytes = PDFEngine.create_searchable_pdf(img_list, ocr_texts)
        media_type = "application/pdf"
        filename = f"{doc.name}_searchable.pdf"
    elif fmt == "pdf":
        out_bytes = PDFEngine.images_to_pdf(img_list)
        media_type = "application/pdf"
        filename = f"{doc.name}.pdf"
    elif fmt in ["jpg", "jpeg", "png", "webp"]:
        if img_list:
            out_bytes = PDFEngine.export_image(img_list[0], fmt)
            media_type = f"image/{fmt}"
            filename = f"{doc.name}_page1.{fmt}"
        else:
            raise HTTPException(status_code=400, detail="No page images found")
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

    if req.compress and media_type == "application/pdf":
        out_bytes = PDFEngine.compress_pdf(out_bytes)

    if req.password and media_type == "application/pdf":
        out_bytes = PDFEngine.protect_pdf(out_bytes, req.password)
        doc.is_password_protected = True
        db.commit()

    db.add(AuditLog(user_id=doc.user_id, action=f"DOCUMENT_EXPORTED: {doc.name} ({fmt})"))
    db.commit()

    return StreamingResponse(
        io.BytesIO(out_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.delete("/delete/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    user_id = doc.user_id
    db.delete(doc)
    db.add(AuditLog(user_id=user_id, action=f"DOCUMENT_DELETED: {doc_id}"))
    db.commit()
    return {"message": "Document deleted successfully"}
