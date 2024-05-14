from typing import List

from pydantic import BaseModel, Field


class Config(BaseModel, extra="ignore"):
    """Plugin Config Here"""

    mixin_source: List[str] = Field(default_factory=list)
    """mixin 数据文件路径（可选），支持 json 格式。"""