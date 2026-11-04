"""Carga y validacion de clausulas.json (ADR-004, D5).

Reglas del archivo:
    - es una lista JSON con al menos una clausula.
Reglas por objeto (en Clausula.__post_init__):
    - los cinco campos existen, son texto y no estan en blanco;
    - clause_id empieza por VRG-;
    - ramo es hogar, auto o comun.
Reglas entre objetos (en cargar_clausulas):
    - clause_id no se repite;
    - titulo y texto no se repiten, salvo entre ramos especificos distintos.
Si alguna regla falla no se devuelve nada: el error lista todos los
problemas encontrados.
"""
import json
from dataclasses import dataclass
from pathlib import Path

NOMBRE_ARCHIVO = "clausulas.json"
CAMPOS = ("clause_id", "documento", "ramo", "titulo", "texto")
# Solo se exige el prefijo, no el patron completo VRG-{CG|POL}-{materia}-{n.m}:
# validarlo entero seria fragil si el formato cambia (decision 4a, Paso 13).
PREFIJO_ID = "VRG-"
# comun vale para cualquier poliza; hogar y auto, solo para su propio ramo.
RAMOS = ("hogar", "auto", "comun")


class ErrorClausulas(Exception):
    """El archivo de clausulas no se puede leer o no es valido."""


# frozen: lo que se valida aqui es lo mismo que luego se hashea y se indexa;
# no debe poder cambiar entre una cosa y la otra.
@dataclass(frozen=True)
class Clausula:
    """Una clausula tal como figura en clausulas.json."""

    clause_id: str
    documento: str
    ramo: str
    titulo: str
    texto: str

    def __post_init__(self) -> None:
        # Las anotaciones de tipo no se comprueban al ejecutar. Este bucle va
        # antes que las otras dos reglas porque ellas dan por hecho que los
        # campos son texto: startswith fallaria con AttributeError si no.
        for campo in CAMPOS:
            valor = getattr(self, campo)
            if not isinstance(valor, str) or not valor.strip():
                raise ErrorClausulas(
                    # !r (repr) muestra el valor entre comillas: deja ver
                    # espacios sobrantes y distingue None de 'None'. Vale para
                    # todos los mensajes de este modulo.
                    f"{self.clause_id!r}: el campo {campo} "
                    "esta vacio o no es texto"
                )
        if not self.clause_id.startswith(PREFIJO_ID):
            raise ErrorClausulas(
                f"{self.clause_id!r}: el identificador debe "
                f"empezar por {PREFIJO_ID}"
            )
        if self.ramo not in RAMOS:
            raise ErrorClausulas(
                f"{self.clause_id!r}: ramo {self.ramo!r} no valido"
            )

    @property
    def texto_indexable(self) -> str:
        """Cadena que se embebe y se hashea: titulo, salto de linea y texto."""
        # El separador queda fijado: cambiarlo cambia todos los hashes y obliga
        # a reindexar. No se anaden ramo ni documento: HOG-7.1 y AUTO-7.1
        # dejarian de tener vectores identicos (ADR-004, D3).
        return f"{self.titulo}\n{self.texto}"


def _crear(elemento: object, posicion: int) -> Clausula:
    """Comprueba la forma de un elemento del JSON y construye la clausula."""
    if not isinstance(elemento, dict):
        raise ErrorClausulas(f"elemento {posicion}: no es un objeto")
    # La forma se comprueba antes de construir: con campos de mas o de menos,
    # Clausula(**elemento) lanzaria TypeError sin decir que elemento falla.
    if set(elemento) != set(CAMPOS):
        raise ErrorClausulas(
            f"elemento {posicion}: los campos deben ser exactamente "
            f"{', '.join(CAMPOS)}"
        )
    return Clausula(**elemento)


def _problemas_ids_repetidos(clausulas: list[Clausula]) -> list[str]:
    vistos = set()
    repetidos = []
    for c in clausulas:
        if c.clause_id in vistos and c.clause_id not in repetidos:
            repetidos.append(c.clause_id)
        vistos.add(c.clause_id)
    return [f"{i!r}: identificador repetido" for i in repetidos]


def _problemas_contenido_repetido(clausulas: list[Clausula]) -> list[str]:
    """Contenido repetido que el filtro por ramo no puede separar.

    El filtro solo separa clausulas de ramos distintos. Si dos clausulas con
    el mismo titulo y texto comparten ramo, o una es comun, la recuperacion
    seria ambigua.
    """
    grupos: dict[tuple[str, str], list[Clausula]] = {}
    for c in clausulas:
        grupos.setdefault((c.titulo, c.texto), []).append(c)
    problemas = []
    for grupo in grupos.values():
        if len(grupo) < 2:
            continue
        ramos = [c.ramo for c in grupo]
        # Permitido: ramos especificos distintos (hogar frente a auto,
        # ADR-004 D2 y D3). comun pasa el filtro de cualquier poliza, asi que
        # choca con todos; un ramo repetido tampoco se separa.
        if "comun" in ramos or len(set(ramos)) != len(ramos):
            ids = ", ".join(c.clause_id for c in grupo)
            problemas.append(f"contenido repetido sin separar por ramo: {ids}")
    return problemas


def cargar_clausulas(directorio: Path) -> list[Clausula]:
    """Lee y valida clausulas.json.

    Parametros:
        directorio: carpeta que contiene clausulas.json.

    Devuelve:
        Lista de clausulas en el orden del archivo.

    Lanza:
        ErrorClausulas: si el archivo no se puede leer o incumple alguna
        regla; en ese caso el mensaje lista todos los problemas.
    """
    ruta = directorio / NOMBRE_ARCHIVO
    try:
        # utf-8 explicito: el valor por defecto en Windows depende de la
        # configuracion regional y el archivo es UTF-8 sin BOM.
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        # Un solo tipo de error para quien llama (precedente: ErrorEmbeddings).
        raise ErrorClausulas(
            f"no se pudo leer {ruta.name}: {error}"
        ) from error
    if not isinstance(datos, list):
        raise ErrorClausulas(f"{ruta.name}: el nivel superior debe ser lista")
    # Un corpus vacio haria que el sistema se abstuviera siempre sin avisar:
    # se falla aqui, cerca de la causa (decision 4 del Paso 13).
    if not datos:
        raise ErrorClausulas(f"{ruta.name}: la lista esta vacia")

    clausulas = []
    problemas = []
    for posicion, elemento in enumerate(datos):
        try:
            clausulas.append(_crear(elemento, posicion))
        except ErrorClausulas as error:
            problemas.append(str(error))
    # Un elemento invalido queda fuera de las reglas entre objetos: sus
    # problemas aparecen en la ejecucion siguiente, al corregir el anterior.
    problemas += _problemas_ids_repetidos(clausulas)
    problemas += _problemas_contenido_repetido(clausulas)

    if problemas:
        lineas = "\n".join(f"- {p}" for p in problemas)
        raise ErrorClausulas(
            f"{ruta.name} no es valido, problemas: {len(problemas)}\n{lineas}"
        )
    return clausulas
