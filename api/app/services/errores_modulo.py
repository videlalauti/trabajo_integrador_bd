"""Excepciones propias de los services de ingresos y transferencias.

Los services no dependen de FastAPI: los routers convierten estas excepciones
al formato de error del contrato compartido.
"""


class RecursoNoEncontrado(Exception):
    """El documento solicitado no existe (se responde 404)."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje
