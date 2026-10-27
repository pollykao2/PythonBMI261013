import unittest
import os
import tempfile

from app import app, bmi_guidance, init_database


class BmiAppTests(unittest.TestCase):
    def setUp(self):
        self.database = tempfile.NamedTemporaryFile(delete=False)
        self.database.close()
        app.config["DATABASE"] = self.database.name
        init_database()
        self.client = app.test_client()

    def tearDown(self):
        os.unlink(self.database.name)

    def test_initial_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("了解自己的<br><em>健康狀況。</em>", page)
        self.assertIn("計算你的 BMI", page)

    def test_calculation_and_advice(self):
        response = self.client.post("/", data={"name": "王小明", "height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn("22.5", page)
        self.assertIn("健康體位", page)
        self.assertIn("維持均衡飲食", page)

    def test_military_service_assessment_is_preliminary_only(self):
        response = self.client.post(
            "/",
            data={"name": "王小明", "height": "170", "weight": "65"},
        )
        page = response.get_data(as_text=True)
        self.assertIn("兵役 BMI 初步評估", page)
        self.assertIn("BMI 為 22.5", page)
        self.assertIn("不是正式的台灣兵役體位分類或判定", page)
        self.assertIn("最新台灣官方規定或主管機關", page)
        self.assertNotIn("正式兵役體位：健康體位", page)

    def test_user_history_lists_saved_records(self):
        self.client.post("/", data={"name": "王小明", "height": "170", "weight": "65"})
        self.client.post("/", data={"name": "王小明", "height": "160", "weight": "60"})

        users_response = self.client.get("/users")
        self.assertEqual(users_response.status_code, 200)
        self.assertIn("王小明", users_response.get_data(as_text=True))

        history_response = self.client.get("/users/王小明")
        history_page = history_response.get_data(as_text=True)
        self.assertEqual(history_response.status_code, 200)
        self.assertIn("22.5", history_page)
        self.assertIn("23.4", history_page)
        self.assertEqual(history_page.count("202"), 2)

    def test_name_is_required(self):
        response = self.client.post("/", data={"height": "170", "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertIn("請輸入使用者名稱", page)
        self.assertNotIn("YOUR RESULT", page)

    def test_taiwan_adult_thresholds(self):
        for bmi, category in [
            (18.4, "體重過輕"),
            (18.5, "健康體位"),
            (23.9, "健康體位"),
            (24.0, "體重過重"),
            (26.9, "體重過重"),
            (27.0, "肥胖"),
        ]:
            with self.subTest(bmi=bmi):
                self.assertEqual(bmi_guidance(bmi)["label"], category)

    def test_invalid_fields_do_not_produce_result(self):
        for height, weight in [("", "65"), ("0", "65"), ("abc", "65"), ("170", "-2"), ("inf", "65"), ("170", "nan"), ("1e-300", "65"), ("1e308", "65"), ("1", "1e308")]:
            with self.subTest(height=height, weight=weight):
                response = self.client.post("/", data={"height": height, "weight": weight})
                page = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn('aria-invalid="true"', page)
                self.assertNotIn("YOUR RESULT", page)

    def test_input_is_escaped(self):
        response = self.client.post("/", data={"height": '<script>alert(1)</script>', "weight": "65"})
        page = response.get_data(as_text=True)
        self.assertNotIn("<script>", page)
        self.assertIn("請輸入大於 0", page)


if __name__ == "__main__":
    unittest.main()
