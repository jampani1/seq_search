"""
Services - Business Logic Layer
================================

Camada de serviços encapsula a lógica de negócio.

DECISÃO TÉCNICA:
----------------
Separar business logic dos endpoints permite:
- Reutilizar lógica em diferentes endpoints
- Testar lógica de negócio isoladamente
- Manter endpoints limpos e focados em HTTP
- Facilitar refatorações futuras
"""

from app.services.sequence_service import SequenceService
from app.services.blast_service import BlastService
from app.services.effector_service import EffectorService
from app.services.grn_service import GRNService

__all__ = ["SequenceService", "BlastService", "EffectorService", "GRNService"]
