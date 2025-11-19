from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from models import db, Company, Plan, Contract, User, Employee, WorkingTimeRecord, PayrollCalculation, LeaveCredit
import os

app = Flask(__name__)

# 設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///employees.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# データベース初期化
db.init_app(app)

# ログイン管理
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'ログインが必要です。'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =============================================================================
# ログイン・ログアウト
# =============================================================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'saas_admin':
            return redirect(url_for('saas_admin_dashboard'))
        else:
            return redirect(url_for('company_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash('アカウントが無効化されています。', 'error')
                return redirect(url_for('login'))

            # 企業管理者の場合、契約チェック
            if user.role == 'company_admin':
                contract = Contract.query.filter_by(
                    company_id=user.company_id,
                    is_active=True
                ).first()

                if not contract:
                    flash('契約情報が見つかりません。管理者にお問い合わせください。', 'error')
                    return redirect(url_for('login'))

                if contract.end_date < date.today():
                    flash('契約期限が切れています。管理者にお問い合わせください。', 'error')
                    return redirect(url_for('login'))

            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            return redirect(url_for('index'))
        else:
            flash('メールアドレスまたはパスワードが正しくありません。', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('login'))

# =============================================================================
# SaaS管理者機能
# =============================================================================

def saas_admin_required(f):
    """SaaS管理者権限チェックデコレータ"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'saas_admin':
            flash('SaaS管理者権限が必要です。', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/saas/dashboard')
@login_required
@saas_admin_required
def saas_admin_dashboard():
    # 統計情報
    total_companies = Company.query.filter_by(is_active=True).count()
    active_contracts = Contract.query.filter_by(is_active=True).filter(
        Contract.end_date >= date.today()
    ).count()
    total_employees = Employee.query.filter_by(status='在籍中').count()

    # 最近の企業
    recent_companies = Company.query.order_by(Company.created_at.desc()).limit(5).all()

    # 契約期限が近い企業（30日以内）
    expiring_soon = Contract.query.filter(
        Contract.is_active == True,
        Contract.end_date >= date.today(),
        Contract.end_date <= date.today() + timedelta(days=30)
    ).all()

    return render_template('saas_admin_dashboard.html',
                         total_companies=total_companies,
                         active_contracts=active_contracts,
                         total_employees=total_employees,
                         recent_companies=recent_companies,
                         expiring_soon=expiring_soon)

@app.route('/saas/companies')
@login_required
@saas_admin_required
def saas_companies():
    companies = Company.query.order_by(Company.created_at.desc()).all()
    return render_template('saas_companies.html', companies=companies)

@app.route('/saas/company/add', methods=['GET', 'POST'])
@login_required
@saas_admin_required
def saas_add_company():
    if request.method == 'POST':
        company_code = request.form.get('company_code')
        company_name = request.form.get('company_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')

        # 管理者情報
        admin_name = request.form.get('admin_name')
        admin_email = request.form.get('admin_email')
        admin_password = request.form.get('admin_password')

        # 契約情報
        plan_id = request.form.get('plan_id')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        billing_cycle = request.form.get('billing_cycle', 'monthly')

        # 終了日を自動計算
        if billing_cycle == 'yearly':
            end_date = start_date + timedelta(days=365)
        else:
            end_date = start_date + timedelta(days=30)

        # 企業作成
        company = Company(
            company_code=company_code,
            company_name=company_name,
            email=email,
            phone=phone,
            address=address
        )
        db.session.add(company)
        db.session.flush()

        # 契約作成
        plan = Plan.query.get(plan_id)
        contract = Contract(
            company_id=company.id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            monthly_fee=plan.monthly_fee if billing_cycle == 'monthly' else plan.yearly_fee,
            billing_cycle=billing_cycle
        )
        db.session.add(contract)

        # 管理者アカウント作成
        admin_user = User(
            email=admin_email,
            password=generate_password_hash(admin_password),
            name=admin_name,
            role='company_admin',
            company_id=company.id
        )
        db.session.add(admin_user)

        db.session.commit()

        flash(f'企業「{company_name}」を登録しました。', 'success')
        return redirect(url_for('saas_companies'))

    plans = Plan.query.filter_by(is_active=True).all()
    return render_template('saas_add_company.html', plans=plans, today=date.today().strftime('%Y-%m-%d'))

@app.route('/saas/company/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
@saas_admin_required
def saas_edit_company(company_id):
    company = Company.query.get_or_404(company_id)

    if request.method == 'POST':
        company.company_name = request.form.get('company_name')
        company.email = request.form.get('email')
        company.phone = request.form.get('phone')
        company.address = request.form.get('address')
        company.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        flash(f'企業「{company.company_name}」を更新しました。', 'success')
        return redirect(url_for('saas_companies'))

    return render_template('saas_edit_company.html', company=company)

@app.route('/saas/plans')
@login_required
@saas_admin_required
def saas_plans():
    plans = Plan.query.all()
    return render_template('saas_plans.html', plans=plans)

@app.route('/saas/plan/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
@saas_admin_required
def saas_edit_plan(plan_id):
    plan = Plan.query.get_or_404(plan_id)

    if request.method == 'POST':
        plan.display_name = request.form.get('display_name')
        plan.max_employees = int(request.form.get('max_employees'))
        plan.monthly_fee = int(request.form.get('monthly_fee'))
        plan.yearly_fee = int(request.form.get('yearly_fee'))
        plan.description = request.form.get('description')
        plan.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        flash(f'プラン「{plan.plan_name}」を更新しました。', 'success')
        return redirect(url_for('saas_plans'))

    return render_template('saas_edit_plan.html', plan=plan)

# =============================================================================
# 企業管理者機能
# =============================================================================

def company_admin_required(f):
    """企業管理者権限チェックデコレータ"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'company_admin':
            flash('企業管理者権限が必要です。', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/company/dashboard')
@login_required
@company_admin_required
def company_dashboard():
    # 統計情報
    total_employees = Employee.query.filter_by(
        company_id=current_user.company_id,
        status='在籍中'
    ).count()

    # 契約情報
    contract = Contract.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).first()

    # 今月の勤怠入力状況
    current_month = date.today().replace(day=1)
    records_count = WorkingTimeRecord.query.filter(
        WorkingTimeRecord.company_id == current_user.company_id,
        WorkingTimeRecord.work_date >= current_month
    ).count()

    return render_template('company_dashboard.html',
                         total_employees=total_employees,
                         contract=contract,
                         records_count=records_count)

@app.route('/employees')
@login_required
@company_admin_required
def employees():
    employees = Employee.query.filter_by(
        company_id=current_user.company_id
    ).order_by(Employee.employee_id).all()

    return render_template('employees.html', employees=employees)

@app.route('/employee/add', methods=['GET', 'POST'])
@login_required
@company_admin_required
def add_employee():
    if request.method == 'POST':
        # 従業員数チェック
        contract = Contract.query.filter_by(
            company_id=current_user.company_id,
            is_active=True
        ).first()

        if contract:
            current_count = Employee.query.filter_by(
                company_id=current_user.company_id,
                status='在籍中'
            ).count()

            if current_count >= contract.plan.max_employees:
                flash(f'従業員数が上限（{contract.plan.max_employees}名）に達しています。', 'error')
                return redirect(url_for('employees'))

        employee = Employee(
            company_id=current_user.company_id,
            employee_id=request.form.get('employee_id'),
            name=request.form.get('name'),
            furigana=request.form.get('furigana'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            birth_date=datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date() if request.form.get('birth_date') else None,
            gender=request.form.get('gender'),
            address=request.form.get('address'),
            join_date=datetime.strptime(request.form.get('join_date'), '%Y-%m-%d').date() if request.form.get('join_date') else None,
            department=request.form.get('department'),
            position=request.form.get('position'),
            employment_type=request.form.get('employment_type'),
            wage_type=request.form.get('wage_type'),
            base_wage=int(request.form.get('base_wage', 0)),
            transportation_allowance=int(request.form.get('transportation_allowance', 0)),
            working_time_system=request.form.get('working_time_system'),
            standard_working_hours=float(request.form.get('standard_working_hours', 8.0)),
            standard_working_days=int(request.form.get('standard_working_days', 5))
        )

        db.session.add(employee)
        db.session.commit()

        flash(f'従業員「{employee.name}」を登録しました。', 'success')
        return redirect(url_for('employees'))

    return render_template('add_employee.html')

@app.route('/employee/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@company_admin_required
def edit_employee(employee_id):
    employee = Employee.query.filter_by(
        id=employee_id,
        company_id=current_user.company_id
    ).first_or_404()

    if request.method == 'POST':
        employee.employee_id = request.form.get('employee_id')
        employee.name = request.form.get('name')
        employee.furigana = request.form.get('furigana')
        employee.email = request.form.get('email')
        employee.phone = request.form.get('phone')
        employee.birth_date = datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date() if request.form.get('birth_date') else None
        employee.gender = request.form.get('gender')
        employee.address = request.form.get('address')
        employee.join_date = datetime.strptime(request.form.get('join_date'), '%Y-%m-%d').date() if request.form.get('join_date') else None
        employee.department = request.form.get('department')
        employee.position = request.form.get('position')
        employee.employment_type = request.form.get('employment_type')
        employee.status = request.form.get('status')
        employee.wage_type = request.form.get('wage_type')
        employee.base_wage = int(request.form.get('base_wage', 0))
        employee.transportation_allowance = int(request.form.get('transportation_allowance', 0))
        employee.working_time_system = request.form.get('working_time_system')
        employee.standard_working_hours = float(request.form.get('standard_working_hours', 8.0))
        employee.standard_working_days = int(request.form.get('standard_working_days', 5))

        db.session.commit()
        flash(f'従業員「{employee.name}」を更新しました。', 'success')
        return redirect(url_for('employees'))

    return render_template('edit_employee.html', employee=employee)

if __name__ == '__main__':
    app.run(debug=True)
