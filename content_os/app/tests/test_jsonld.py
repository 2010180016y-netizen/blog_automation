import unittest
from app.schema.product_jsonld import ProductJsonLdGenerator
from app.schema.validate import SchemaValidator

class TestJsonLd(unittest.TestCase):
    def setUp(self):
        self.generator = ProductJsonLdGenerator()
        self.validator = SchemaValidator()

    def test_valid_product_generation(self):
        data = {
            "sku": "SKU123",
            "name": "Test Product",
            "image_url": "https://example.com/img.jpg",
            "description": "A great product",
            "price": 10000,
            "currency": "KRW",
            "url": "https://example.com/p/SKU123"
        }
        jsonld = self.generator.generate(data)
        self.assertEqual(jsonld["name"], "Test Product")
        self.assertEqual(jsonld["offers"]["price"], 10000)
        
        report = self.validator.validate_product(jsonld)
        self.assertTrue(report["valid"])

    def test_invalid_product_validation(self):
        data = {
            "sku": "SKU123",
            # "name" is missing
            "price": 10000
        }
        jsonld = self.generator.generate(data)
        report = self.validator.validate_product(jsonld)
        self.assertFalse(report["valid"])
        self.assertIn("Missing required field: name", report["errors"])

if __name__ == "__main__":
    unittest.main()
