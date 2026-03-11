"""
tests/test_almacen.py
Tests para el sistema de almacén del refugio (engine/almacen.py).
"""
import unittest

from engine.personaje import Sobreviviente
from engine.almacen import (
    agregar_item,
    quitar_item,
    depositar_al_almacen,
    transferir_al_inventario,
    almacen_vacio,
    buscar_nombre,
    cantidad_total_tipo,
)


def _personaje() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.inventario.clear()
    p.almacen.clear()
    return p


class TestAgregarItem(unittest.TestCase):

    def test_agregar_item_no_stackable(self):
        almacen = almacen_vacio()
        item = {"id": "cuchillo", "nombre": "Cuchillo", "tipo": "arma_cortante"}
        agregar_item(almacen, item)
        self.assertEqual(len(almacen), 1)
        self.assertEqual(almacen[0]["nombre"], "Cuchillo")

    def test_agregar_item_stackable_se_apila(self):
        almacen = almacen_vacio()
        item1 = {"id": "manzana", "nombre": "Manzana", "tipo": "comida", "cantidad": 2}
        item2 = {"id": "manzana", "nombre": "Manzana", "tipo": "comida", "cantidad": 3}
        agregar_item(almacen, item1)
        agregar_item(almacen, item2)
        self.assertEqual(len(almacen), 1)
        self.assertEqual(almacen[0]["cantidad"], 5)

    def test_agregar_item_stackable_sin_cantidad_usa_uno(self):
        almacen = almacen_vacio()
        item = {"id": "bala", "nombre": "Bala 9mm", "tipo": "municion"}
        agregar_item(almacen, item)
        self.assertEqual(almacen[0]["cantidad"], 1)

    def test_agregar_dos_items_distintos(self):
        almacen = almacen_vacio()
        agregar_item(almacen, {"id": "a", "nombre": "Agua", "tipo": "agua", "cantidad": 1})
        agregar_item(almacen, {"id": "b", "nombre": "Pan", "tipo": "comida", "cantidad": 1})
        self.assertEqual(len(almacen), 2)

    def test_agregar_no_muta_original(self):
        almacen = almacen_vacio()
        item = {"id": "cuchillo", "nombre": "Cuchillo", "tipo": "arma_cortante"}
        agregar_item(almacen, item)
        # Modificar el original no afecta al almacén
        item["nombre"] = "Otro"
        self.assertEqual(almacen[0]["nombre"], "Cuchillo")


class TestQuitarItem(unittest.TestCase):

    def test_quitar_item_existente(self):
        almacen = [{"id": "cuchillo", "nombre": "Cuchillo", "tipo": "arma_cortante"}]
        quitado = quitar_item(almacen, "Cuchillo")
        self.assertIsNotNone(quitado)
        self.assertEqual(quitado["nombre"], "Cuchillo")
        self.assertEqual(len(almacen), 0)

    def test_quitar_item_inexistente(self):
        almacen = [{"id": "cuchillo", "nombre": "Cuchillo", "tipo": "arma_cortante"}]
        quitado = quitar_item(almacen, "Espada")
        self.assertIsNone(quitado)
        self.assertEqual(len(almacen), 1)

    def test_quitar_parcial_stackable(self):
        almacen = [{"id": "bala", "nombre": "Bala 9mm", "tipo": "municion", "cantidad": 5}]
        quitado = quitar_item(almacen, "Bala 9mm", 2)
        self.assertIsNotNone(quitado)
        self.assertEqual(quitado["cantidad"], 2)
        self.assertEqual(almacen[0]["cantidad"], 3)

    def test_quitar_toda_cantidad_stackable(self):
        almacen = [{"id": "bala", "nombre": "Bala 9mm", "tipo": "municion", "cantidad": 3}]
        quitado = quitar_item(almacen, "Bala 9mm", 3)
        self.assertIsNotNone(quitado)
        self.assertEqual(len(almacen), 0)


class TestDepositarAlAlmacen(unittest.TestCase):

    def test_depositar_item_del_inventario(self):
        p = _personaje()
        p.inventario.append({"id": "agua", "nombre": "Botella de agua", "tipo": "agua", "cantidad": 2})
        almacen = almacen_vacio()
        exito, msg = depositar_al_almacen(p, almacen, "Botella de agua", 1)
        self.assertTrue(exito)
        self.assertEqual(len(almacen), 1)
        self.assertIn("depositaste", msg.lower())

    def test_depositar_item_inexistente_falla(self):
        p = _personaje()
        almacen = almacen_vacio()
        exito, msg = depositar_al_almacen(p, almacen, "Item Fantasma")
        self.assertFalse(exito)

    def test_depositar_reduce_inventario(self):
        p = _personaje()
        p.inventario.append({"id": "agua", "nombre": "Botella de agua", "tipo": "agua", "cantidad": 3})
        almacen = almacen_vacio()
        depositar_al_almacen(p, almacen, "Botella de agua", 1)
        inv_item = next((i for i in p.inventario if i["nombre"] == "Botella de agua"), None)
        self.assertIsNotNone(inv_item)
        self.assertEqual(inv_item["cantidad"], 2)


class TestTransferirAlInventario(unittest.TestCase):

    def test_transferir_al_inventario(self):
        p = _personaje()
        almacen = [{"id": "vendaje", "nombre": "Vendaje", "tipo": "medicina", "cantidad": 1, "peso": 0.1}]
        exito, msg = transferir_al_inventario(almacen, p, "Vendaje")
        self.assertTrue(exito)
        self.assertEqual(len(almacen), 0)
        nombres_inv = [i.get("nombre") for i in p.inventario]
        self.assertIn("Vendaje", nombres_inv)

    def test_transferir_item_inexistente_falla(self):
        p = _personaje()
        almacen = almacen_vacio()
        exito, msg = transferir_al_inventario(almacen, p, "Nada")
        self.assertFalse(exito)


class TestAlmacenVacio(unittest.TestCase):

    def test_almacen_vacio_retorna_lista(self):
        a = almacen_vacio()
        self.assertIsInstance(a, list)
        self.assertEqual(len(a), 0)


class TestBuscarNombre(unittest.TestCase):

    def test_buscar_existente(self):
        almacen = [{"id": "x", "nombre": "Lata de atún", "tipo": "comida"}]
        found = buscar_nombre(almacen, "Lata de atún")
        self.assertIsNotNone(found)
        self.assertEqual(found["id"], "x")

    def test_buscar_inexistente(self):
        almacen = [{"id": "x", "nombre": "Lata de atún", "tipo": "comida"}]
        found = buscar_nombre(almacen, "Espada")
        self.assertIsNone(found)


class TestCantidadTotalTipo(unittest.TestCase):

    def test_cuenta_total(self):
        almacen = [
            {"id": "a", "nombre": "Manzana", "tipo": "comida", "cantidad": 3},
            {"id": "b", "nombre": "Pan", "tipo": "comida", "cantidad": 2},
            {"id": "c", "nombre": "Vendaje", "tipo": "medicina", "cantidad": 1},
        ]
        self.assertEqual(cantidad_total_tipo(almacen, "comida"), 5)
        self.assertEqual(cantidad_total_tipo(almacen, "medicina"), 1)
        self.assertEqual(cantidad_total_tipo(almacen, "arma"), 0)


if __name__ == "__main__":
    unittest.main()
