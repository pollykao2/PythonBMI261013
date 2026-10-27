import math
import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager

from flask import Flask, render_template, request

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get(
    "DATABASE", os.path.join(app.root_path, "instance", "bmi.sqlite3")
)


@contextmanager
def get_database():
    database_path = app.config["DATABASE"]
    database_directory = os.path.dirname(database_path)
    if database_directory:
        os.makedirs(database_directory, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_database():
    with get_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bmi_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                bmi REAL NOT NULL,
                calculated_at TEXT NOT NULL
            )
            """
        )


def list_users():
    init_database()
    with get_database() as connection:
        return connection.execute(
            """
            SELECT user_name, COUNT(*) AS record_count
            FROM bmi_records
            GROUP BY user_name
            ORDER BY user_name COLLATE NOCASE
            """
        ).fetchall()


def list_user_records(user_name):
    init_database()
    with get_database() as connection:
        return connection.execute(
            """
            SELECT bmi, calculated_at
            FROM bmi_records
            WHERE user_name = ?
            ORDER BY calculated_at DESC, id DESC
            """,
            (user_name,),
        ).fetchall()


def bmi_guidance(bmi):
    if bmi < 18.5:
        return {
            "label": "體重過輕",
            "tone": "low",
            "advice": "留意是否攝取足夠且均衡的營養，規律進食並搭配適度肌力活動；若體重持續下降，建議諮詢醫師或營養師。",
        }
    if bmi < 24:
        return {
            "label": "健康體位",
            "tone": "healthy",
            "advice": "維持均衡飲食與規律運動，並持續留意睡眠及生活習慣，幫助保持健康體位。",
        }
    if bmi < 27:
        return {
            "label": "體重過重",
            "tone": "high",
            "advice": "可從減少含糖飲料、增加蔬菜與日常活動量開始，循序建立適合自己的健康習慣。",
        }
    return {
        "label": "肥胖",
        "tone": "high",
        "advice": "建議與醫師或營養師討論適合自己的飲食及運動計畫，並留意血壓、血糖等健康指標。",
    }


def military_service_assessment(height, weight, bmi):
    return {
        "title": "兵役 BMI 初步評估",
        "summary": (
            f"依你提供的身高 {height:g} 公分與體重 {weight:g} 公斤，"
            f"計算 BMI 為 {bmi:.1f}。"
        ),
        "disclaimer": "此結果僅供初步參考，不是正式的台灣兵役體位分類或判定。",
        "guidance": "正式資格與體位請以最新台灣官方規定或主管機關、授權機構的認定為準。",
    }


def parse_positive_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


@app.route("/", methods=["GET", "POST"])
def index():
    init_database()
    users = list_users()
    name_input = ""
    height_input = ""
    weight_input = ""
    errors = {}
    result = None

    if request.method == "POST":
        name_input = request.form.get("name", "").strip()
        height_input = request.form.get("height", "").strip()
        weight_input = request.form.get("weight", "").strip()
        height = parse_positive_number(height_input)
        weight = parse_positive_number(weight_input)

        if not name_input:
            errors["name"] = "請輸入使用者名稱。"
        elif len(name_input) > 80:
            errors["name"] = "使用者名稱不可超過 80 個字元。"
        if height is None:
            errors["height"] = "請輸入大於 0 的有效身高（公分）。"
        if weight is None:
            errors["weight"] = "請輸入大於 0 的有效體重（公斤）。"

        if not errors:
            height_meters = height / 100
            height_squared = height_meters * height_meters
            if not math.isfinite(height_squared) or height_squared == 0:
                errors["height"] = "無法使用這組數值計算 BMI，請檢查身高與體重。"
            else:
                bmi = weight / height_squared
                if not math.isfinite(bmi) or bmi == 0:
                    errors["weight"] = "無法使用這組數值計算 BMI，請檢查身高與體重。"
                else:
                    displayed_bmi = round(bmi, 1)
                    result = {
                        "bmi": f"{displayed_bmi:.1f}",
                        **bmi_guidance(displayed_bmi),
                        "military_assessment": military_service_assessment(
                            height, weight, displayed_bmi
                        ),
                    }
                    with get_database() as connection:
                        connection.execute(
                            """
                            INSERT INTO bmi_records (user_name, bmi, calculated_at)
                            VALUES (?, ?, ?)
                            """,
                            (
                                name_input,
                                displayed_bmi,
                                datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                            ),
                        )
                    users = list_users()

    return render_template(
        "index.html",
        users=users,
        name_input=name_input,
        height_input=height_input,
        weight_input=weight_input,
        errors=errors,
        result=result,
    )


@app.route("/users")
def users():
    return render_template("users.html", users=list_users())


@app.route("/users/<user_name>")
def user_history(user_name):
    records = list_user_records(user_name)
    if not records:
        return render_template("users.html", users=list_users()), 404
    return render_template(
        "user_history.html",
        user_name=user_name,
        records=records,
        users=list_users(),
    )


if __name__ == "__main__":
    app.run(debug=True)
