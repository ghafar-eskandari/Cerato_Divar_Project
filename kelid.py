from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import pandas as pd
import time
import re


# ============================================================
# 1. تنظیمات
# ============================================================

url = "https://divar.ir/s/tehran/car/kia/cerato-ir/optional-automatic-2000cc"

OUTPUT_FILE = "cerato_divar_tehran.csv"

SCROLL_COUNT = 30
SCROLL_STEP = 800
SCROLL_WAIT = 2


# ============================================================
# 2. مسیر ChromeDriver موجود روی سیستم
# ============================================================

DRIVER_PATH = (
    r"C:\Users\Setareh14-User\.wdm\drivers\chromedriver\win64"
    r"\154.0.8037.92\chromedriver-win64\chromedriver.exe"
)


# ============================================================
# 3. باز کردن Chrome
# ============================================================

print("=" * 50)
print("شروع برنامه")
print("=" * 50)

print("\nراه‌اندازی ChromeDriver...")

service = Service(DRIVER_PATH)

ch = webdriver.Chrome(service=service)

print("Chrome با موفقیت باز شد.")

ch.get(url)

print("\nصفحه دیوار باز شد...")
time.sleep(5)


# ============================================================
# 4. جمع‌آوری آگهی‌ها
# ============================================================

all_ads = {}

print("\nشروع جمع‌آوری آگهی‌ها...\n")


for i in range(SCROLL_COUNT):

    links = ch.find_elements(
        By.CSS_SELECTOR,
        'a[href*="/v/"]'
    )

    new_count = 0

    for link in links:

        try:

            href = link.get_attribute("href")

            text = link.text.strip()

            if href and "/v/" in href and text:

                if href not in all_ads:

                    all_ads[href] = {
                        "text": text,
                        "url": href
                    }

                    new_count += 1

        except Exception:

            continue


    print(
        f"اسکرول {i + 1:02d} | "
        f"آگهی جدید: {new_count} | "
        f"کل آگهی‌ها: {len(all_ads)}"
    )


    ch.execute_script(
        f"window.scrollBy(0, {SCROLL_STEP});"
    )

    time.sleep(SCROLL_WAIT)


print("\n" + "=" * 50)
print(
    f"تعداد کل آگهی‌های جمع‌آوری‌شده: "
    f"{len(all_ads)}"
)
print("=" * 50)


# ============================================================
# 5. تبدیل اعداد فارسی و عربی به انگلیسی
# ============================================================

digit_map = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789"
)


# ============================================================
# 6. استخراج اطلاعات ساختاریافته
# ============================================================

ads = []

print("\nشروع استخراج اطلاعات...\n")


for href, item in all_ads.items():

    text = item["text"]


    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]


    if not lines:

        continue


    # --------------------------------------------------------
    # عنوان
    # --------------------------------------------------------

    title = lines[0]


    # --------------------------------------------------------
    # نرمال‌سازی اعداد
    # --------------------------------------------------------

    normalized_text = text.translate(digit_map)


    # --------------------------------------------------------
    # سال مدل
    # --------------------------------------------------------

    year = ""


    year_match = re.search(
        r'(?:مدل\s*)?(13\d{2}|14\d{2})',
        normalized_text
    )


    if year_match:

        year = int(
            year_match.group(1)
        )


    else:

        year_match = re.search(
            r'(?:مدل\s*)?([9][0-9])',
            normalized_text
        )


        if year_match:

            year = 1300 + int(
                year_match.group(1)
            )


        else:

            year_match = re.search(
                r'\b(20[0-2][0-9])\b',
                normalized_text
            )


            if year_match:

                year = int(
                    year_match.group(1)
                )


    # --------------------------------------------------------
    # کارکرد
    # --------------------------------------------------------

    mileage = ""


    mileage_match = re.search(
        r'([\d,]+)\s*کیلومتر',
        normalized_text
    )


    if mileage_match:

        mileage = int(
            mileage_match.group(1)
            .replace(",", "")
        )


    # --------------------------------------------------------
    # قیمت
    # --------------------------------------------------------

    price = ""


    price_match = re.search(
        r'([\d,]+)\s*تومان',
        normalized_text
    )


    if price_match:

        price = int(
            price_match.group(1)
            .replace(",", "")
        )


    # --------------------------------------------------------
    # زمان و مکان
    # --------------------------------------------------------

    time_info = ""

    location = ""


    combined_patterns = [

        r'^(دقایقی پیش)\s+در\s+(.+)$',

        r'^(نیم ساعت پیش)\s+در\s+(.+)$',

        r'^(\d+\s+دقیقه پیش)\s+در\s+(.+)$',

        r'^(\d+\s+ساعت پیش)\s+در\s+(.+)$',

        r'^(\d+\s+روز پیش)\s+در\s+(.+)$',

        r'^(\d+\s+هفته پیش)\s+در\s+(.+)$'

    ]


    for line in lines:

        normalized_line = (
            line
            .translate(digit_map)
            .strip()
        )


        matched = False


        for pattern in combined_patterns:

            match = re.match(
                pattern,
                normalized_line
            )


            if match:

                time_info = (
                    match.group(1)
                    .strip()
                )

                location = (
                    match.group(2)
                    .strip()
                )

                matched = True

                break


        if matched:

            continue


        # ----------------------------------------------------
        # زمان به صورت مستقل
        # ----------------------------------------------------

        if not time_info:

            time_patterns = [

                r'^دقایقی پیش$',

                r'^نیم ساعت پیش$',

                r'^\d+\s+دقیقه پیش$',

                r'^\d+\s+ساعت پیش$',

                r'^\d+\s+روز پیش$',

                r'^\d+\s+هفته پیش$'

            ]


            for pattern in time_patterns:

                if re.match(
                    pattern,
                    normalized_line
                ):

                    time_info = normalized_line

                    break


    # --------------------------------------------------------
    # مکان مستقل: نمایشگاه در ...
    # --------------------------------------------------------

    if not location:

        for line in lines:

            clean_line = line.strip()


            match = re.match(
                r'^نمایشگاه\s+در\s+(.+)$',
                clean_line
            )


            if match:

                location = (
                    match.group(1)
                    .strip()
                )

                break


    # --------------------------------------------------------
    # مکان مستقل: در ...
    # --------------------------------------------------------

    if not location:

        for line in lines:

            clean_line = line.strip()


            if (
                "پیش" in clean_line
                or "دقایقی" in clean_line
                or "نیم ساعت" in clean_line
            ):

                continue


            match = re.match(
                r'^در\s+(.+)$',
                clean_line
            )


            if match:

                possible_location = (
                    match.group(1)
                    .strip()
                )


                if (
                    "تومان"
                    not in possible_location
                    and
                    "کیلومتر"
                    not in possible_location
                ):

                    location = (
                        possible_location
                    )

                    break


    # --------------------------------------------------------
    # ساخت رکورد
    # --------------------------------------------------------

    record = {

        "title": title,

        "year": year,

        "mileage": mileage,

        "price": price,

        "location": location,

        "time": time_info,

        "url": href

    }


    ads.append(record)


# ============================================================
# 7. نمایش تعداد واقعی رکوردهای استخراج‌شده
# ============================================================

print("\n" + "=" * 50)
print("استخراج اطلاعات با موفقیت انجام شد.")
print("=" * 50)

print(
    f"\nتعداد آگهی‌های جمع‌آوری‌شده: "
    f"{len(all_ads)}"
)

print(
    f"تعداد رکوردهای استخراج‌شده: "
    f"{len(ads)}"
)


# ============================================================
# 8. تبدیل به DataFrame
# ============================================================

df = pd.DataFrame(ads)


# ============================================================
# 9. اطمینان از ترتیب ستون‌ها
# ============================================================

columns = [

    "title",

    "year",

    "mileage",

    "price",

    "location",

    "time",

    "url"

]


df = df[columns]


# ============================================================
# 10. حذف رکوردهای تکراری بر اساس URL
# ============================================================

before_duplicate_removal = len(df)


df = df.drop_duplicates(
    subset=["url"],
    keep="first"
)


after_duplicate_removal = len(df)


print("\n" + "=" * 50)
print("بررسی تکراری‌ها")
print("=" * 50)


print(
    f"قبل از حذف URLهای تکراری: "
    f"{before_duplicate_removal}"
)


print(
    f"بعد از حذف URLهای تکراری: "
    f"{after_duplicate_removal}"
)


# ============================================================
# 11. ذخیره CSV
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 12. گزارش نهایی
# ============================================================

print("\n" + "=" * 50)
print("فایل CSV ساخته شد")
print("=" * 50)


print(
    f"نام فایل: {OUTPUT_FILE}"
)

print(
    f"تعداد رکورد: {len(df)}"
)

print(
    f"تعداد ستون: {len(df.columns)}"
)


print("\nستون‌ها:")


for column in df.columns:

    print(f"- {column}")


# ============================================================
# 13. نمایش 10 رکورد اول
# ============================================================

print("\n" + "=" * 50)
print("10 رکورد اول")
print("=" * 50)


for index, row in df.head(10).iterrows():

    print("\n------------------------")

    print(
        f"آگهی: {index + 1}"
    )

    print(
        f"عنوان: {row['title']}"
    )

    print(
        f"سال مدل: {row['year']}"
    )

    print(
        f"کارکرد: {row['mileage']}"
    )

    print(
        f"قیمت: {row['price']}"
    )

    print(
        f"مکان: {row['location']}"
    )

    print(
        f"زمان: {row['time']}"
    )

    print(
        f"URL: {row['url']}"
    )


# ============================================================
# 14. بستن Chrome
# ============================================================

ch.quit()


print("\n" + "=" * 50)
print("برنامه با موفقیت به پایان رسید.")
print("=" * 50)