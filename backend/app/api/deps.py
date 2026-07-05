from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_api_key


DbSession = Annotated[Session, Depends(get_db)]
ApiKey = Annotated[None, Depends(require_api_key)]
