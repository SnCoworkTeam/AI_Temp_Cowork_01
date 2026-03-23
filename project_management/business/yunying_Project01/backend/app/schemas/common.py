from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")

class ResponseBase(BaseModel):
    success: bool = True
    message: str = ""

class DataResponse(ResponseBase, GenericModel, Generic[T]):
    data: Optional[T] = None
