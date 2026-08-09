from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    size: int
    download_url: Optional[str] = None
    doc_type: str
