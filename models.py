from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic_core import core_schema


class _ObjectIdPydanticAnnotation:

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate(v):
            if isinstance(v, ObjectId):
                return str(v)
            if isinstance(v, str) and ObjectId.is_valid(v):
                return v
            raise ValueError("ID inválido de MongoDB (ObjectId)")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )


PyObjectId = Annotated[str, _ObjectIdPydanticAnnotation]


class MembresiaBase(BaseModel):
    nombre_usuario: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nombre completo del usuario afiliado al gimnasio",
        example="Carlos Andres Mendoza",
    )
    plan_suscripcion: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Tipo de plan contratado (Mensual, Trimestral, Semestral, Anual, Black)",
        example="Trimestral",
    )
    meses_duracion: int = Field(
        ..., gt=0, le=36, description="Duración de la suscripción en meses", example=3
    )
    activo: bool = Field(
        default=True, description="Estado actual de vigencia de la membresía"
    )


class MembresiaCreate(MembresiaBase):
    pass


class MembresiaUpdate(BaseModel):

    nombre_usuario: Optional[str] = Field(None, min_length=3, max_length=100)
    plan_suscripcion: Optional[str] = Field(None, min_length=3, max_length=50)
    meses_duracion: Optional[int] = Field(None, gt=0, le=36)
    activo: Optional[bool] = None


class Membresia(MembresiaBase):

    id: PyObjectId = Field(
        alias="_id", description="Identificador único ObjectId de MongoDB"
    )
    fecha_creacion: datetime = Field(
        default_factory=datetime.now, description="Fecha y hora de registro"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "654321789abcdef012345678",
                "nombre_usuario": "Carlos Andres Mendoza",
                "plan_suscripcion": "Trimestral",
                "meses_duracion": 3,
                "activo": True,
                "fecha_creacion": "2026-11-13T10:30:00",
            }
        },
    )
