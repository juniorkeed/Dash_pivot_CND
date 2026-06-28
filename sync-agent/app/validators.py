"""Validadores de entrada para proteger queries contra SQL injection.

Cópia literal de utils/validators.py do projeto Streamlit (não dependia de nada
do projeto). Usado ao interpolar listas em cláusulas SQL `IN (...)`.
"""
from collections.abc import Iterable


def sanitize_int_list(values: Iterable, field_name: str = "values") -> list[int]:
    """Garante que `values` é uma lista de inteiros.

    Usado antes de interpolar listas em cláusulas SQL `IN (...)` — Oracle não
    aceita bind variables para listas, então a defesa é validação estrita de tipo.

    Raises:
        ValueError: se algum elemento não puder ser convertido para int.
    """
    if values is None:
        return []
    sanitized: list[int] = []
    for v in values:
        if isinstance(v, bool):
            raise ValueError(f"{field_name} contém valor booleano inválido: {v!r}")
        if isinstance(v, float):
            # int(1.5) truncaria silenciosamente; rejeitamos para não corromper filtros.
            raise ValueError(f"{field_name} contém valor float inválido: {v!r}")
        try:
            sanitized.append(int(v))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} contém valor não-numérico: {v!r}"
            ) from exc
    return sanitized


def sanitize_str_list(
    values: Iterable,
    field_name: str = "values",
    max_len: int = 50,
) -> list[str]:
    """Garante que `values` é uma lista de strings curtas, não-vazias e únicas.

    Usado para validar valores que virão como bind variables (ex.: CODFAB).
    Não escapa caracteres — o bind variable cuida disso. Apenas rejeita
    valores anômalos cedo (None, vazios, longos demais) e remove duplicatas
    preservando a ordem de primeira ocorrência.
    """
    if values is None:
        return []
    sanitized: list[str] = []
    seen: set[str] = set()
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if not s:
            continue
        if len(s) > max_len:
            raise ValueError(f"{field_name} contém valor muito longo: {s!r}")
        if s in seen:
            continue
        seen.add(s)
        sanitized.append(s)
    return sanitized
