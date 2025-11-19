from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

# 会社マスタ
class Company(db.Model):
    __tablename__ = 'company'

    id = db.Column(db.Integer, primary_key=True)
    company_code = db.Column(db.String(50), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーション
    users = db.relationship('User', backref='company', lazy=True)
    employees = db.relationship('Employee', backref='company', lazy=True)
    contracts = db.relationship('Contract', backref='company', lazy=True)

# プラン定義
class Plan(db.Model):
    __tablename__ = 'plan'

    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(50), unique=True, nullable=False)  # Basic, Standard, Premium
    display_name = db.Column(db.String(100), nullable=False)
    max_employees = db.Column(db.Integer, nullable=False)
    monthly_fee = db.Column(db.Integer, nullable=False)  # 月額料金（円）
    yearly_fee = db.Column(db.Integer)  # 年額料金（円）
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 契約管理
class Contract(db.Model):
    __tablename__ = 'contract'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    monthly_fee = db.Column(db.Integer)  # 契約時の月額（プラン変更履歴用）
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly / yearly
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    plan = db.relationship('Plan', backref='contracts')

# ユーザー（SaaS管理者・企業管理者のみ）
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), nullable=False)  # saas_admin, company_admin
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

# 従業員マスタ
class Employee(db.Model):
    __tablename__ = 'employee'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    employee_id = db.Column(db.String(50))  # 社員番号
    name = db.Column(db.String(100), nullable=False)
    furigana = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(500))
    join_date = db.Column(db.Date)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    employment_type = db.Column(db.String(50))  # 正社員、契約社員、パート等
    status = db.Column(db.String(20), default='在籍中')  # 在籍中、退職

    # 給与関連
    wage_type = db.Column(db.String(20))  # monthly, hourly, daily
    base_wage = db.Column(db.Integer)  # 基本給（月給・時給・日給）
    transportation_allowance = db.Column(db.Integer, default=0)  # 通勤手当

    # 勤務形態
    working_time_system = db.Column(db.String(50))  # standard, flex等
    standard_working_hours = db.Column(db.Float, default=8.0)  # 1日の所定労働時間
    standard_working_days = db.Column(db.Integer, default=5)  # 週の所定労働日数

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    working_time_records = db.relationship('WorkingTimeRecord', backref='employee', lazy=True)
    payroll_calculations = db.relationship('PayrollCalculation', backref='employee', lazy=True)
    leave_credits = db.relationship('LeaveCredit', backref='employee', lazy=True)

# 労働時間記録
class WorkingTimeRecord(db.Model):
    __tablename__ = 'working_time_record'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    work_date = db.Column(db.Date, nullable=False)

    # 勤務時間
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    break_minutes = db.Column(db.Integer, default=0)

    # 計算結果（時間単位）
    regular_hours = db.Column(db.Float, default=0)  # 法定内労働時間
    overtime_in_legal = db.Column(db.Float, default=0)  # 法定内残業
    overtime_out_legal = db.Column(db.Float, default=0)  # 法定外残業
    legal_holiday_hours = db.Column(db.Float, default=0)  # 法定休日労働
    non_legal_holiday_hours = db.Column(db.Float, default=0)  # 法定外休日労働
    late_night_hours = db.Column(db.Float, default=0)  # 深夜労働

    # 欠勤・休暇
    is_absent = db.Column(db.Boolean, default=False)
    is_paid_leave = db.Column(db.Boolean, default=False)
    leave_days = db.Column(db.Float, default=0)  # 有給取得日数（0.5, 1.0等）

    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 給与計算結果
class PayrollCalculation(db.Model):
    __tablename__ = 'payroll_calculation'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    # 支給項目
    base_salary = db.Column(db.Integer, default=0)  # 基本給
    overtime_pay = db.Column(db.Integer, default=0)  # 残業手当
    transportation = db.Column(db.Integer, default=0)  # 通勤手当
    other_allowances = db.Column(db.Integer, default=0)  # その他手当
    gross_salary = db.Column(db.Integer, default=0)  # 総支給額

    # 控除項目
    health_insurance = db.Column(db.Integer, default=0)  # 健康保険
    pension = db.Column(db.Integer, default=0)  # 厚生年金
    employment_insurance = db.Column(db.Integer, default=0)  # 雇用保険
    income_tax = db.Column(db.Integer, default=0)  # 所得税
    resident_tax = db.Column(db.Integer, default=0)  # 住民税
    other_deductions = db.Column(db.Integer, default=0)  # その他控除
    total_deductions = db.Column(db.Integer, default=0)  # 控除合計

    # 差引支給額
    net_salary = db.Column(db.Integer, default=0)

    # 勤怠集計
    total_working_days = db.Column(db.Integer, default=0)
    total_working_hours = db.Column(db.Float, default=0)
    paid_leave_days = db.Column(db.Float, default=0)
    absent_days = db.Column(db.Integer, default=0)

    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 有給休暇付与
class LeaveCredit(db.Model):
    __tablename__ = 'leave_credit'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    grant_date = db.Column(db.Date, nullable=False)  # 付与日
    days_granted = db.Column(db.Float, nullable=False)  # 付与日数
    expiry_date = db.Column(db.Date)  # 有効期限
    days_used = db.Column(db.Float, default=0)  # 使用日数
    days_remaining = db.Column(db.Float)  # 残日数
    fiscal_year = db.Column(db.Integer)  # 年度
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
