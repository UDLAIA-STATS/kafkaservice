# Create your models here.
from pydantic import BaseModel


class Jugadores(BaseModel):
    idjugador: int
    idbanner: str
    nombrejugador: str
    apellidojugador: str
    numerocamisetajugador: int
    imagenjugador: bytes | None = None
    posicionjugador: str
    jugadoractivo: bool = False
