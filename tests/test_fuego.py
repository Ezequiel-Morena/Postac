"""
tests/test_fuego.py
Tests para el sistema de fuego y combustión (engine/fuego.py).
"""
import unittest
from unittest.mock import patch

from engine.personaje import Sobreviviente
from engine.fuego import (
    encender_fuego,
    tick_fuego,
    puede_cocinar,
    esta_encendido,
    combustible_disponible,
    apagar_fuego,
    agregar_combustible,
)


def _personaje(**overrides) -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.inventario.clear()
    p.almacen.clear()
    p.fuego_activo = False
    p.combustible_restante = 0
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


class TestEncenderFuego(unittest.TestCase):

    @patch("engine.fuego.random.random", return_value=0.01)
    def test_encender_con_encendedor_y_madera(self, _mock):
        p = _personaje()
        p.inventario.append({"id": "encendedor", "nombre": "Encendedor"})
        p.inventario.append({"id": "madera", "nombre": "Madera"})
        exito, msg = encender_fuego(p)
        self.assertTrue(exito)
        self.assertTrue(p.fuego_activo)
        self.assertGreater(p.combustible_restante, 0)
        self.assertIn("🔥", msg)

    @patch("engine.fuego.random.random", return_value=0.99)
    def test_encender_sin_materiales_usa_friccion_y_puede_fallar(self, _mock):
        """Sin encendedor ni pedernal usa fricción (prob 0.20) — con random=0.99 falla."""
        p = _personaje()
        p.inventario.append({"id": "madera", "nombre": "Madera"})
        exito, msg = encender_fuego(p)
        self.assertFalse(exito)
        self.assertFalse(p.fuego_activo)

    def test_encender_sin_combustible_falla(self):
        p = _personaje()
        p.inventario.append({"id": "encendedor", "nombre": "Encendedor"})
        # Sin madera/leña/carbón
        exito, msg = encender_fuego(p)
        self.assertFalse(exito)
        self.assertIn("combustible", msg.lower())

    @patch("engine.fuego.random.random", return_value=0.01)
    def test_encender_con_pedernal(self, _mock):
        p = _personaje()
        p.inventario.append({"id": "pedernal", "nombre": "Pedernal"})
        p.inventario.append({"id": "lena", "nombre": "Leña"})
        exito, msg = encender_fuego(p)
        self.assertTrue(exito)
        self.assertTrue(p.fuego_activo)


class TestTickFuego(unittest.TestCase):

    def test_tick_reduce_combustible(self):
        p = _personaje()
        p.fuego_activo = True
        p.combustible_restante = 60
        tick_fuego(p, 0.5)  # 30 minutos
        self.assertEqual(p.combustible_restante, 30)
        self.assertTrue(p.fuego_activo)

    def test_tick_apaga_fuego_sin_combustible(self):
        p = _personaje()
        p.fuego_activo = True
        p.combustible_restante = 30
        tick_fuego(p, 1.0)  # 60 minutos > 30 disponibles
        self.assertFalse(p.fuego_activo)
        self.assertEqual(p.combustible_restante, 0)

    def test_tick_sin_fuego_no_hace_nada(self):
        p = _personaje()
        p.fuego_activo = False
        p.combustible_restante = 0
        tick_fuego(p, 1.0)
        self.assertFalse(p.fuego_activo)
        self.assertEqual(p.combustible_restante, 0)


class TestPuedeCocinar(unittest.TestCase):

    def test_puede_cocinar_con_fuego_activo(self):
        p = _personaje()
        p.fuego_activo = True
        p.combustible_restante = 50
        self.assertTrue(puede_cocinar(p))

    def test_no_puede_cocinar_sin_fuego(self):
        p = _personaje()
        p.fuego_activo = False
        self.assertFalse(puede_cocinar(p))


class TestEstaEncendido(unittest.TestCase):

    def test_esta_encendido_true(self):
        p = _personaje()
        p.fuego_activo = True
        self.assertTrue(esta_encendido(p))

    def test_esta_encendido_false(self):
        p = _personaje()
        p.fuego_activo = False
        self.assertFalse(esta_encendido(p))


class TestCombustibleDisponible(unittest.TestCase):

    def test_retorna_combustible_restante(self):
        p = _personaje()
        p.combustible_restante = 45
        self.assertEqual(combustible_disponible(p), 45)

    def test_retorna_cero_sin_combustible(self):
        p = _personaje()
        p.combustible_restante = 0
        self.assertEqual(combustible_disponible(p), 0)


class TestApagarFuego(unittest.TestCase):

    def test_apagar_fuego(self):
        p = _personaje()
        p.fuego_activo = True
        p.combustible_restante = 50
        apagar_fuego(p)
        self.assertFalse(p.fuego_activo)
        self.assertEqual(p.combustible_restante, 0)


class TestAgregarCombustible(unittest.TestCase):

    @patch("engine.fuego.random.random", return_value=0.01)
    def test_agregar_madera_al_fuego(self, _mock):
        p = _personaje()
        p.fuego_activo = True
        p.combustible_restante = 10
        p.inventario.append({"id": "madera", "nombre": "Madera"})
        exito, msg = agregar_combustible(p, "madera")
        self.assertTrue(exito)
        self.assertEqual(p.combustible_restante, 40)  # 10 + 30 (madera)

    def test_agregar_sin_fuego_falla(self):
        p = _personaje()
        p.fuego_activo = False
        p.inventario.append({"id": "madera", "nombre": "Madera"})
        exito, msg = agregar_combustible(p, "madera")
        self.assertFalse(exito)


if __name__ == "__main__":
    unittest.main()
