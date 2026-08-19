from datetime import datetime

from pydantic import BaseModel    


class RunCreate(BaseModel):
    method_type: str
    request_data: str
    response_data: str
    status: str
    started_at: datetime
    ended_at: datetime



class RunRespBase(BaseModel):
    id: int
    method_type: str
    status: str


class RunResponse(RunRespBase):
    request_data: str
    response_data: str
    started_at: datetime
    ended_at: datetime