import flet as ft
import sqlite3
import os
from datetime import datetime

if os.environ.get("FLET_APP_STORAGE_DATA"):
    DB_PATH = os.path.join(os.environ["FLET_APP_STORAGE_DATA"], "kosti_hospital.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kosti_hospital.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE,
            phone_number TEXT,
            registered_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            national_id TEXT,
            clinic_name TEXT,
            doctor_name TEXT,
            appointment_date TEXT,
            ticket_price TEXT,
            image_path TEXT,
            booked_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def show_snack(page, text, color=ft.Colors.BLUE_700):
    snack = ft.SnackBar(
        content=ft.Text(text, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=color,
        duration=3000
    )
    page.show_dialog(snack)
    page.update()

def show_login_screen(page):
    page.clean()
    name_field = ft.TextField(label="الاسم الكامل", expand=True, text_align=ft.TextAlign.RIGHT)
    nat_field = ft.TextField(label="الرقم الوطني", expand=True, keyboard_type=ft.KeyboardType.NUMBER, max_length=11)
    phone_field = ft.TextField(label="رقم الهاتف", expand=True, keyboard_type=ft.KeyboardType.PHONE, max_length=10)
    
    def handle_login(ev):
        name = (name_field.value or "").strip()
        nat = (nat_field.value or "").strip()
        phone = (phone_field.value or "").strip()
        if not name or not nat or not phone:
            show_snack(page, "⚠️ أدخل جميع البيانات", ft.Colors.RED_600)
            return
        if len(nat) != 11 or not nat.isdigit():
            show_snack(page, "⚠️ الرقم الوطني 11 رقماً", ft.Colors.RED_600)
            return
        if len(phone) != 10 or not phone.startswith("09"):
            show_snack(page, "⚠️ رقم الهاتف غير صحيح", ft.Colors.RED_600)
            return
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id FROM patients WHERE national_id = ?", (nat,))
        user = cursor.fetchone()
        if not user:
            cursor.execute("""INSERT INTO patients 
                (national_id, phone_number, registered_at) VALUES (?, ?, ?)""",
                (nat, phone, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
        conn.close()
        show_clinics_screen(page, name, nat)
        
    page.add(ft.Column([
        ft.Text("مستشفى كوستي التعليمي", size=22, weight=ft.FontWeight.BOLD),
        name_field, nat_field, phone_field,
        ft.Button(content="تسجيل الدخول", on_click=handle_login,
                  expand=True, height=50, bgcolor=ft.Colors.BLUE_600,
                  color=ft.Colors.WHITE)
    ], spacing=12))
    page.update()

def show_clinics_screen(page, name, nat):
    page.clean()
    clinics = ["عيادة الباطنية", "عيادة الجراحة", "عيادة الأطفال", "عيادة النساء والتوليد"]
    buttons = []
    for c in clinics:
        def make_handler(clinic_name):
            def handler(ev):
                show_doctors_screen(page, clinic_name, name, nat)
            return handler
        buttons.append(ft.Button(
            content=c, on_click=make_handler(c),
            expand=True, height=45,
            bgcolor=ft.Colors.BLUE_50, color=ft.Colors.BLUE_900
        ))
    page.add(ft.Column([
        ft.Text(f"مرحباً: {name}", size=14, color=ft.Colors.GREEN_700),
        ft.Text("اختر العيادة المطلوبة", size=20, weight=ft.FontWeight.BOLD),
        *buttons
    ], spacing=10, expand=True))
    page.update()

def show_doctors_screen(page, clinic, name, nat):
    page.clean()
    doctors_data = {
        "عيادة الباطنية": ("محمد أحمد", "باطنية", "الأحد - الخميس", "8 ص - 2 م"),
        "عيادة الجراحة": ("أمير محمد", "جراحة عامة", "السبت - الأربعاء", "8 ص - 2 م"),
        "عيادة الأطفال": ("سلمى خالد", "طب الأطفال", "الأحد - الخميس", "9 ص - 3 م"),
        "عيادة النساء والتوليد": ("هند عمر", "نساء وتوليد", "الأحد - الخميس", "9 ص - 3 م"),
    }
    doc_name, spec, days, hours = doctors_data.get(clinic, ("", "", "", ""))
    ticket_price = "10,000 جنيه"
    
    def book(ev):
        show_booking_screen(page, clinic, doc_name, spec, nat, name, ticket_price)
        
    page.add(ft.Column([
        ft.Text(f"أطباء {clinic}", size=18, weight=ft.FontWeight.BOLD),
        ft.Container(
            content=ft.Column([
                ft.Text(f"{doc_name} / {clinic}", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(f"{spec} — {days} — {hours}", size=12),
                ft.Text(f"💵 رسوم التذكرة: {ticket_price}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                ft.Button(content="📅 حجز موعد", on_click=book,
                          expand=True, height=42,
                          bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
            ], spacing=8),
            padding=15, bgcolor=ft.Colors.BLUE_50, border_radius=12
        ),
        ft.TextButton(content="← العودة للعيادات",
                      on_click=lambda e: show_clinics_screen(page, name, nat))
    ], spacing=15))
    page.update()

def show_booking_screen(page, clinic, doctor, spec, nat, name, price):
    page.clean()
    name_field = ft.TextField(label="اسم المريض", value=name, expand=True)
    date_field = ft.TextField(label="تاريخ الموعد", expand=True)
    
    attached_image_status = ft.Text("لم يتم إرفاق صورة", size=12, color=ft.Colors.GREY_700)
    uploaded_file_path = {"path": ""}

    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            uploaded_file_path["path"] = e.files[0].name
            attached_image_status.value = f"📎 تم إرفاق: {e.files[0].name}"
            attached_image_status.color = ft.Colors.GREEN_700
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def confirm_booking(ev):
        date_val = (date_field.value or "").strip()
        if not date_val:
            show_snack(page, "⚠️ أدخل التاريخ", ft.Colors.RED_600)
            return
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO appointments 
            (patient_name, national_id, clinic_name, doctor_name,
             appointment_date, ticket_price, image_path, booked_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, nat, clinic, doctor, date_val, price,
             uploaded_file_path["path"],
             datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        show_snack(page, "✅ تم تأكيد الحجز بنجاح", ft.Colors.GREEN_600)
        show_my_appointments_screen(page, nat)

    page.add(ft.Column([
        ft.Text("حجز موعد جديد", size=20, weight=ft.FontWeight.BOLD),
        ft.Text(f"💰 قيمة التذكرة: {price}", size=16, color=ft.Colors.BLUE_900, weight=ft.FontWeight.
