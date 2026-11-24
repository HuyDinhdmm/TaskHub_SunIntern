from pydantic import BaseModel, ConfigDict, Field


class LabelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#3B82F6", max_length=20)


class LabelUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(..., max_length=20)


class LabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    color: str
