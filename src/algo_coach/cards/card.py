from pydantic import BaseModel, Field


class Card(BaseModel):
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
