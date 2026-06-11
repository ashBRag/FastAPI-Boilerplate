from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database.session import async_session

AsyncSessionDep = Annotated[AsyncSession, Depends(async_session)]