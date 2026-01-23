# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Union

from pydantic import BaseModel, Field


class Record(BaseModel):
    signal: str = Field(..., description="e.g. 'ecg','acc','hr','hr_est'")
    ts: Union[int, float, None] = Field(None, description="Epoch ts (ms/us/ns/s)")
    
    class Config:
        extra = "allow"


class IngestResponse(BaseModel):
    accepted: int
    file: str
