from codiri.src.model.common import (
    MapImpl,
    FixedMap,
    ValidatingMap,
    ValidatingFixedMap,
)
import unittest


class TestMap(unittest.TestCase):
    def test_init_str(self):
        map_types = [MapImpl, ValidatingMap]
        for map_type in map_types:
            with self.subTest():
                self.assertEqual(str(map_type()), "{}")
                self.assertEqual(str(map_type(("a",))), "{'a': None}")
                self.assertEqual(
                    str(map_type(("a", "b"))), "{'a': None, 'b': None}"
                )


class TestMapImpl(unittest.TestCase):
    def test_iter_setitem_getitem(self):
        map_impl = MapImpl()
        map_impl["a"] = 1
        map_impl["b"] = 2
        ref = {"a": 1, "b": 2}
        for key in map_impl:
            self.assertEqual(map_impl[key], ref[key])

    def test_initialized(self):
        map_impl = MapImpl(("1", "2"))
        self.assertFalse(map_impl.initialized())
        map_impl["1"] = 1
        self.assertFalse(map_impl.initialized())
        map_impl["2"] = 2
        self.assertTrue(map_impl.initialized())


class TestFixedMap(unittest.TestCase):
    def test_init_str(self):
        self.assertEqual(str(FixedMap(("a",))), "{'a': None}")
        self.assertEqual(str(FixedMap(("a", "b"))), "{'a': None, 'b': None}")

    def test_setitem(self):
        fmap = FixedMap(("a", "b"))
        fmap["a"] = 1
        fmap["b"] = 2
        with self.assertRaises(KeyError):
            fmap["c"] = 3


class TestValidatingMap(unittest.TestCase):
    def test_setitem(self):
        vmap = ValidatingMap()

        def validator(x):
            return x > 0

        vmap["a"] = (1, validator, str())
        self.assertEqual(vmap["a"], 1)
        with self.assertRaises(ValueError):
            vmap["a"] = (-1, validator, str())
        self.assertEqual(vmap["a"], 1)


class TestValidatingFixedMap(unittest.TestCase):
    def test_setitem(self):
        vfmap = ValidatingFixedMap(("a", "b"))

        def validator(x):
            return x > 0

        vfmap["a"] = (1, validator, str())
        vfmap["b"] = (2, validator, str())
        self.assertEqual(vfmap["a"], 1)
        self.assertEqual(vfmap["b"], 2)
        with self.assertRaises(KeyError):
            vfmap["c"] = (3, validator, str())
        with self.assertRaises(ValueError):
            vfmap["a"] = (-1, validator, str())
        with self.assertRaises((ValueError, KeyError)):
            vfmap["c"] = (-1, validator, str())
