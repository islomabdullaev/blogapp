from typing import Type, TypeVar, Generic, Optional
from datetime import datetime
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from pydantic import BaseModel as PydanticBaseModel

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def create(self, obj_in: T) -> T:
        if isinstance(obj_in, PydanticBaseModel):
            obj_data_dict = obj_in.model_dump(exclude_unset=True)
        else:
            obj_data_dict = obj_in

        obj = self.model.model_validate(obj_data_dict)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get(self, obj_id) -> Optional[T]:
        statement = select(self.model).where(self.model.id == obj_id, self.model.is_deleted == False)
        result = await self.db.exec(statement)
        return result.first()

    async def list(self) -> list[T]:
        statement = select(self.model).where(self.model.is_deleted == False)
        result = await self.db.exec(statement)
        return result.all()

    async def update(self, obj: T, obj_data: dict | PydanticBaseModel) -> T:
        if isinstance(obj_data, PydanticBaseModel):
            obj_data_dict = obj_data.model_dump(exclude_unset=True)
        else:
            obj_data_dict = obj_data
        for field, value in obj_data_dict.items():
            if value is not None:
                setattr(obj, field, value)
        obj.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: T):
        obj.is_deleted = True # for soft delete purpose
        await self.db.commit()
        await self.db.refresh(obj)
