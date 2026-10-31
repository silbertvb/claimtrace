"""Puerto de embeddings: convierte textos en vectores.

Este modulo no depende de ningun proveedor (no importa `openai`). Quien lo use
(el indexador, /retrieve, las pruebas con falsos) solo conoce este contrato.
`core/` no conoce conceptos de seguros (ADR-003): aqui solo hay textos y vectores.
"""

from abc import ABC, abstractmethod


class ErrorEmbeddings(Exception):
    """Fallo al obtener embeddings.

    Se usa tanto para las validaciones del adaptador (clave ausente, entrada
    vacia, respuesta incoherente) como para envolver los errores del proveedor.
    Quien llama captura solo este tipo y no necesita importar el SDK.
    """


class EmbeddingProvider(ABC):
    """Contrato de un proveedor de embeddings.

    Cada subclase debe definir `modelo`, `dimensiones` y `embed`. Si falta
    alguno, crear el objeto falla con TypeError.
    """

    @property
    @abstractmethod
    def modelo(self) -> str:
        """Nombre del modelo que genera los vectores."""

    @property
    @abstractmethod
    def dimensiones(self) -> int:
        """Longitud de cada vector que devuelve `embed`."""

    @abstractmethod
    def embed(self, textos: list[str]) -> list[list[float]]:
        """Convierte cada texto en un vector.

        Devuelve una lista con un vector por texto, en el mismo orden que
        `textos`. Lanza ErrorEmbeddings si no puede cumplirlo.
        """