from pydantic import BaseModel, Field


class StoryboardRequest(BaseModel):
    destination: str = Field(default="Your destination", max_length=100)
    trip_description: str = Field(default="", max_length=2000)
    mood: str = Field(default="cinematic", max_length=60)
    target_duration_seconds: int = Field(default=45, ge=15, le=180)
    aspect_ratio: str = Field(default="9:16", pattern=r"^(9:16|16:9|1:1)$")


class RenderRequest(BaseModel):
    asset_ids: list[str] = Field(min_length=1, max_length=30)
    aspect_ratio: str = Field(default="9:16", pattern=r"^(9:16|16:9|1:1)$")
    title: str = Field(default="My trip", max_length=80)
    clip_seconds: int = Field(default=5, ge=2, le=15)
