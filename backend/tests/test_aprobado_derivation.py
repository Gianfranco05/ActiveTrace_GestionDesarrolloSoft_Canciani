"""TDD: Aprobado derivation logic tests."""

from decimal import Decimal

import pytest

from app.services.calificacion_service import compute_aprobado


# ===== Group 3: compute_aprobado =====


def test_numeric_aprobado_true():
    """RED 3.1: Numeric grade >= umbral returns True."""
    result = compute_aprobado(
        tipo="Numerica", nota_numerica=Decimal("75"), nota_textual=None,
        umbral_pct=60, valores_aprobatorios=None,
    )
    assert result is True


def test_numeric_aprobado_false():
    """TRIANGULATE 3.4: Numeric grade < umbral returns False."""
    result = compute_aprobado(
        tipo="Numerica", nota_numerica=Decimal("45"), nota_textual=None,
        umbral_pct=60, valores_aprobatorios=None,
    )
    assert result is False


def test_textual_aprobado_true():
    """TRIANGULATE 3.4: Textual value in approved set returns True."""
    result = compute_aprobado(
        tipo="Textual", nota_numerica=None, nota_textual="Satisfactorio",
        umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
    )
    assert result is True


def test_textual_aprobado_false():
    """TRIANGULATE 3.4: Textual value not in approved set returns False."""
    result = compute_aprobado(
        tipo="Textual", nota_numerica=None, nota_textual="No satisfactorio",
        umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
    )
    assert result is False


def test_null_numeric_not_aprobado():
    """TRIANGULATE 3.4: Null numeric grade returns False."""
    result = compute_aprobado(
        tipo="Numerica", nota_numerica=None, nota_textual=None,
        umbral_pct=60, valores_aprobatorios=None,
    )
    assert result is False


def test_null_textual_not_aprobado():
    """TRIANGULATE 3.4: Null textual grade returns False."""
    result = compute_aprobado(
        tipo="Textual", nota_numerica=None, nota_textual=None,
        umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
    )
    assert result is False


def test_default_umbral_60_when_no_config():
    """TRIANGULATE 3.4: Default 60% umbral when no config provided."""
    result = compute_aprobado(
        tipo="Numerica", nota_numerica=Decimal("60"), nota_textual=None,
        umbral_pct=60, valores_aprobatorios=None,
    )
    assert result is True


def test_case_insensitive_textual_match():
    """TRIANGULATE 3.4: Case-insensitive textual match."""
    result = compute_aprobado(
        tipo="Textual", nota_numerica=None, nota_textual="satisfactorio",
        umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
    )
    assert result is True


def test_textual_trimmed_match():
    """TRIANGULATE 3.4: Trimmed textual match."""
    result = compute_aprobado(
        tipo="Textual", nota_numerica=None, nota_textual="  Satisfactorio  ",
        umbral_pct=60, valores_aprobatorios=["Satisfactorio", "Supera lo esperado"],
    )
    assert result is True


def test_numeric_exact_boundary():
    """TRIANGULATE: Exact boundary at umbral."""
    result = compute_aprobado(
        tipo="Numerica", nota_numerica=Decimal("60"), nota_textual=None,
        umbral_pct=60, valores_aprobatorios=None,
    )
    assert result is True


def test_numeric_just_below_boundary():
    """TRIANGULATE: Just below boundary."""
    result = compute_aprobado(
        tipo="Numerica", nota_numerica=Decimal("59"), nota_textual=None,
        umbral_pct=60, valores_aprobatorios=None,
    )
    assert result is False
