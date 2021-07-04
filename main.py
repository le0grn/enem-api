from os import environ
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio

app = FastAPI()
readOnlyConnection = "mongodb+srv://api:w7LLs2483RTNj72p@cluster0.mptel.mongodb.net/questions?retryWrites=true&w=majority"
client = motor.motor_asyncio.AsyncIOMotorClient(readOnlyConnection)
if "MONGODB_URL" in environ:
    client = motor.motor_asyncio.AsyncIOMotorClient(environ["MONGODB_URL"])
db = client.questions


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class Alternativa(BaseModel):
    texto: str
    isCorrect: bool

class QuestionModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    ano: str = Field(...)
    materia: str = Field(...)
    titulo: str = Field(...)
    texto: str = Field(...)
    fonte: str = Field(...)
    enunciado: str = Field(...)
    alternativas: List[Alternativa]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "ano": "2019",
                "materia": "portugues",
                "titulo": "blabla",
                "texto": "blablablabla",
                "fonte": "bla",
                "enunciado": "blablabla",
                "alternativas": [
                    {
                        "texto": "blablabla",
                        "isCorrect": "true"
                    },
                    {
                        "texto": "blabla",
                        "isCorrect": "false"
                    },
                    {
                        "texto": "blabla",
                        "isCorrect": "false"
                    },
                    {
                        "texto": "blabla",
                        "isCorrect": "false"
                    },
                    {
                        "texto": "blabla",
                        "isCorrect": "false"
                    }
                ]
            }
        }

@app.post("/", response_description="Adicionar nova questão", response_model=QuestionModel)
async def create_question(question: QuestionModel = Body(...)):
    question = jsonable_encoder(question)
    new_question = await db["questions"].insert_one(question)
    created_question = await db["questions"].find_one({"_id": new_question.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_question)


@app.get(
    "/", response_description="List all questions", response_model=List[QuestionModel]
)
async def list_questions():
    questions = await db["questions"].find().to_list(1000)
    return questions

@app.delete("/{id}", response_description="Delete a question")
async def delete_question(id: str):
    delete_result = await db["questions"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Question {id} not found")
