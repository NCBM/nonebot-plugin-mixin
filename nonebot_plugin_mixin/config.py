from typing import List
from pydantic import BaseModel, Extra, Field


class Config(BaseModel, extra=Extra.ignore):
    """Plugin Config Here"""

    mixin_source: List[str] = Field(default_factory=list)
    """mixin 数据文件路径（可选），支持 json 格式。"""