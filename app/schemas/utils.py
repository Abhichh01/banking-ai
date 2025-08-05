"""
Schema utilities and helpers
"""
from typing import Type, TypeVar, Any, Dict, Union, List, Optional
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
import json

T = TypeVar('T', bound=BaseModel)

def to_camel_case(string: str) -> str:
    """Convert snake_case to camelCase"""
    parts = string.split('_')
    return parts[0] + ''.join(part.capitalize() for part in parts[1:])

def to_snake_case(string: str) -> str:
    """Convert camelCase to snake_case"""
    return ''.join(['_' + c.lower() if c.isupper() else c for c in string]).lstrip('_')

def model_to_dict(
    model: BaseModel,
    *,
    exclude_unset: bool = False,
    exclude_none: bool = True,
    by_alias: bool = True,
    exclude: Optional[set] = None
) -> Dict[str, Any]:
    """Convert Pydantic model to dict with configurable options"""
    return model.dict(
        exclude_unset=exclude_unset,
        exclude_none=exclude_none,
        by_alias=by_alias,
        exclude=exclude or set()
    )

def model_to_json(
    model: BaseModel,
    *,
    indent: Optional[int] = None,
    **kwargs
) -> str:
    """Convert Pydantic model to JSON string"""
    return model.json(indent=indent, **kwargs)

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling special types"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def parse_json(json_data: Union[str, bytes, bytearray]) -> Dict[str, Any]:
    """Parse JSON with custom decoder"""
    if isinstance(json_data, (bytes, bytearray)):
        json_data = json_data.decode('utf-8')
    return json.loads(json_data)

def create_response_schema(
    model: Type[T],
    name: str = None,
    description: str = None,
    **kwargs
) -> Type[BaseModel]:
    """Dynamically create a response schema"""
    class_name = name or f"{model.__name__}Response"
    return type(
        class_name,
        (model,),
        {
            "__annotations__": {
                **model.__annotations__,
                **kwargs
            },
            "__doc__": description or f"Response schema for {model.__name__}",
        }
    )
