from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from bson import ObjectId
from datetime import datetime

from models import Membresia, MembresiaCreate, MembresiaUpdate
from database import coleccion_membresias, verificar_conexion


app = FastAPI(
    title="API Gestión de Gimnasio / Fitness - SENA ADSO",
    description="API RESTful asíncrona con FastAPI y MongoDB (FARM Stack) para control de membresías.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.on_event("startup")
async def startup_db_client():
    await verificar_conexion()


@app.get("/", tags=["Raíz"])
async def root():
    return {
        "mensaje": "Bienvenido a la API Asíncrona de Membresías de Gimnasio (SENA ADSO)",
        "aprendiz": "Erik Thomas Espitia Ariza",
        "documentacion": "/docs"
    }


@app.post(
    "/membresias",
    response_model=Membresia,
    status_code=status.HTTP_201_CREATED,
    tags=["Membresías"],
    summary="Registrar una nueva membresía en MongoDB"
)
async def create_membresia(membresia_in: MembresiaCreate):

    membresia_existente = await coleccion_membresias.find_one(
        {"nombre_usuario": membresia_in.nombre_usuario}
    )
    if membresia_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una membresía registrada para el usuario '{membresia_in.nombre_usuario}'."
        )

    nueva_membresia = membresia_in.model_dump()
    nueva_membresia["fecha_creacion"] = datetime.now()

    resultado = await coleccion_membresias.insert_one(nueva_membresia)
    membresia_creada = await coleccion_membresias.find_one({"_id": resultado.inserted_id})
    return membresia_creada


@app.get(
    "/membresias",
    response_model=List[Membresia],
    status_code=status.HTTP_200_OK,
    tags=["Membresías"],
    summary="Listar todas las membresías"
)
async def get_membresias():
    membresias = []
    cursor = coleccion_membresias.find()
    async for documento in cursor:
        membresias.append(documento)
    return membresias


@app.get(
    "/membresias/{id}",
    response_model=Membresia,
    status_code=status.HTTP_200_OK,
    tags=["Membresías"],
    summary="Buscar membresía por ObjectId"
)
async def get_membresia_por_id(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido de MongoDB."
        )

    membresia = await coleccion_membresias.find_one({"_id": ObjectId(id)})
    if membresia:
        return membresia

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"La membresía con ID '{id}' no fue encontrada en la base de datos."
    )


@app.put(
    "/membresias/{id}",
    response_model=Membresia,
    status_code=status.HTTP_200_OK,
    tags=["Membresías"],
    summary="Actualizar datos o estado de una membresía"
)
async def update_membresia(id: str, membresia_update: MembresiaUpdate):
    """Actualiza parcialmente los campos de un documento en MongoDB por su _id."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido."
        )

    datos_a_actualizar = membresia_update.model_dump(exclude_unset=True)

    if len(datos_a_actualizar) >= 1:
        resultado_actualizacion = await coleccion_membresias.update_one(
            {"_id": ObjectId(id)},
            {"$set": datos_a_actualizar}
        )

        if resultado_actualizacion.modified_count == 1 or resultado_actualizacion.matched_count == 1:
            membresia_modificada = await coleccion_membresias.find_one({"_id": ObjectId(id)})
            return membresia_modificada

    membresia_existente = await coleccion_membresias.find_one({"_id": ObjectId(id)})
    if membresia_existente:
        return membresia_existente

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible actualizar. La membresía con ID '{id}' no existe."
    )


@app.delete(
    "/membresias/{id}",
    status_code=status.HTTP_200_OK,
    tags=["Membresías"],
    summary="Eliminar membresía de MongoDB"
)
async def delete_membresia(id: str):
    """Elimina permanentemente un documento de MongoDB por su ObjectId."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido."
        )

    resultado_eliminacion = await coleccion_membresias.delete_one({"_id": ObjectId(id)})

    if resultado_eliminacion.deleted_count == 1:
        return {"mensaje": f"Membresía con ID '{id}' eliminada exitosamente de MongoDB."}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible eliminar. La membresía con ID '{id}' no existe en la base de datos."
    )