import unittest
import tempfile
import os
from PIL import Image
from business_card_scanner import BusinessCardScanner

class TestBusinessCardScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = BusinessCardScanner()
        # ダミー画像用の一時ファイル作成
        self.temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        # 空の画像を生成
        Image.new("RGB", (100, 50), color="white").save(self.temp_image.name)
        self.temp_image.close()

    def tearDown(self):
        if os.path.exists(self.temp_image.name):
            os.remove(self.temp_image.name)

    def test_guess_reading(self):
        family_name, given_name = self.scanner.guess_reading("大西 諒", "ry0024@g.ecc.u-tokyo.ac.jpb")
        self.assertTrue(family_name)
        self.assertTrue(given_name)

    def test_create_multiple_vcards(self):
        # サンプルレスポンス（geminiから返ってくるJSONを想定）
        samples = [
            {
                "name": "大西 諒",
                "email": "ry0024@g.ecc.u-tokyo.ac.jpb",
                "company": "東京大学",
                "title": "教養学部(前期課程)",
                "postal_code": "〒153-8902",
                "address": "東京都目黒区駒場3-8-1",
                "phone": "03-5454-6014",
                "social_links": []
            },
            {
                "name": "藤本 淳史",
                "email": "a_fujimoto@led-tokyo.co.jp",
                "company": "LED TOKYO 株式会社",
                "title": "LED TOKYO研究室",
                "postal_code": "151-0051",
                "address": "東京都渋谷区千駄ヶ谷3丁目16-18",
                "phone": "03-6804-5393",
                "social_links": []
            },
            {
                "name": "鈴木 直樹",
                "email": "suzuki@led-tokyo.co.jp",
                "company": "LED TOKYO 株式会社",
                "title": "代表取締役 CEO",
                "postal_code": "151-0051",
                "address": "東京都渋谷区千駄ヶ谷3丁目16-18",
                "phone": "03-6804-5393",
                "social_links": []
            }
        ]
        # 各サンプルについてvCard文字列を生成し、必要な項目が含まれることを検証
        for sample in samples:
            vcard = self.scanner.create_vcard(sample, self.temp_image.name)
            self.assertIn(sample["name"], vcard)
            self.assertIn(sample["email"], vcard)
            self.assertIn(sample["postal_code"], vcard)
            self.assertIn(sample["address"], vcard)
            self.assertIn(sample["phone"], vcard)
            self.assertIn(sample["company"], vcard)
            self.assertIn(sample["title"], vcard)

if __name__ == '__main__':
    unittest.main()
