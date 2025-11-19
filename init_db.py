from app import app, db
from models import Company, Plan, Contract, User, Employee, WorkingTimeRecord, PayrollCalculation, LeaveCredit
from werkzeug.security import generate_password_hash
from datetime import date, datetime, timedelta

with app.app_context():
    print("データベースを初期化しています...")

    # テーブル作成
    db.create_all()
    print("✓ テーブルを作成しました")

    # プランが存在しない場合のみ作成
    if Plan.query.count() == 0:
        print("\nデフォルトプランを作成しています...")

        plans = [
            Plan(
                plan_name='basic',
                display_name='ベーシック',
                max_employees=10,
                monthly_fee=5000,
                yearly_fee=50000,
                description='小規模企業向けの基本プラン',
                is_active=True
            ),
            Plan(
                plan_name='standard',
                display_name='スタンダード',
                max_employees=50,
                monthly_fee=15000,
                yearly_fee=150000,
                description='中規模企業向けの標準プラン',
                is_active=True
            ),
            Plan(
                plan_name='premium',
                display_name='プレミアム',
                max_employees=200,
                monthly_fee=40000,
                yearly_fee=400000,
                description='大規模企業向けの上位プラン',
                is_active=True
            )
        ]

        for plan in plans:
            db.session.add(plan)

        db.session.commit()
        print("✓ 3つのプランを作成しました")
    else:
        print("\n✓ プランは既に存在します")

    # SaaS管理者アカウントが存在しない場合のみ作成
    saas_admin = User.query.filter_by(role='saas_admin').first()
    if not saas_admin:
        print("\nSaaS管理者アカウントを作成しています...")

        saas_admin = User(
            email='saas@example.com',
            password=generate_password_hash('saasadmin123'),
            name='SaaS管理者',
            role='saas_admin',
            is_active=True
        )
        db.session.add(saas_admin)
        db.session.commit()

        print("✓ SaaS管理者アカウントを作成しました")
        print("  メール: saas@example.com")
        print("  パスワード: saasadmin123")
    else:
        print("\n✓ SaaS管理者アカウントは既に存在します")

    # テスト企業が存在しない場合のみ作成
    test_company = Company.query.filter_by(company_code='TEST001').first()
    if not test_company:
        print("\nテスト企業を作成しています...")

        # 企業作成
        test_company = Company(
            company_code='TEST001',
            company_name='テスト株式会社',
            email='test@example.com',
            phone='03-1234-5678',
            address='東京都渋谷区1-1-1',
            is_active=True
        )
        db.session.add(test_company)
        db.session.flush()

        # 契約作成（スタンダードプラン、30日間）
        standard_plan = Plan.query.filter_by(plan_name='standard').first()
        if standard_plan:
            contract = Contract(
                company_id=test_company.id,
                plan_id=standard_plan.id,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                monthly_fee=standard_plan.monthly_fee,
                billing_cycle='monthly',
                is_active=True
            )
            db.session.add(contract)

        # 企業管理者アカウント作成
        company_admin = User(
            email='admin@test.com',
            password=generate_password_hash('admin123'),
            name='管理者太郎',
            role='company_admin',
            company_id=test_company.id,
            is_active=True
        )
        db.session.add(company_admin)

        db.session.commit()

        print("✓ テスト企業を作成しました")
        print("  企業名: テスト株式会社")
        print("  企業コード: TEST001")
        print("  プラン: スタンダード（従業員上限50名）")
        print("  契約期限: 30日間")
        print("\n  管理者アカウント:")
        print("  メール: admin@test.com")
        print("  パスワード: admin123")

        # サンプル従業員を作成
        print("\nサンプル従業員を作成しています...")

        sample_employees = [
            {
                'employee_id': 'EMP001',
                'name': '田中 太郎',
                'furigana': 'タナカ タロウ',
                'email': 'tanaka@test.com',
                'phone': '080-1111-2222',
                'birth_date': date(1990, 4, 15),
                'gender': '男性',
                'address': '東京都新宿区1-1-1',
                'join_date': date(2020, 4, 1),
                'department': '営業部',
                'position': '課長',
                'employment_type': '正社員',
                'status': '在籍中',
                'wage_type': 'monthly',
                'base_wage': 350000,
                'transportation_allowance': 15000,
                'working_time_system': 'standard',
                'standard_working_hours': 8.0,
                'standard_working_days': 5
            },
            {
                'employee_id': 'EMP002',
                'name': '佐藤 花子',
                'furigana': 'サトウ ハナコ',
                'email': 'sato@test.com',
                'phone': '080-3333-4444',
                'birth_date': date(1992, 8, 22),
                'gender': '女性',
                'address': '東京都渋谷区2-2-2',
                'join_date': date(2021, 7, 1),
                'department': '人事部',
                'position': '主任',
                'employment_type': '正社員',
                'status': '在籍中',
                'wage_type': 'monthly',
                'base_wage': 300000,
                'transportation_allowance': 12000,
                'working_time_system': 'standard',
                'standard_working_hours': 8.0,
                'standard_working_days': 5
            },
            {
                'employee_id': 'EMP003',
                'name': '鈴木 次郎',
                'furigana': 'スズキ ジロウ',
                'email': 'suzuki@test.com',
                'phone': '080-5555-6666',
                'birth_date': date(1995, 12, 10),
                'gender': '男性',
                'address': '東京都品川区3-3-3',
                'join_date': date(2022, 10, 1),
                'department': '営業部',
                'position': '一般',
                'employment_type': '正社員',
                'status': '在籍中',
                'wage_type': 'monthly',
                'base_wage': 250000,
                'transportation_allowance': 10000,
                'working_time_system': 'standard',
                'standard_working_hours': 8.0,
                'standard_working_days': 5
            }
        ]

        for emp_data in sample_employees:
            employee = Employee(
                company_id=test_company.id,
                **emp_data
            )
            db.session.add(employee)

            # 有給休暇付与（入社日基準で10日付与）
            leave_credit = LeaveCredit(
                company_id=test_company.id,
                employee_id=employee.id,
                days_granted=10,
                grant_date=emp_data['join_date'],
                days_remaining=10,
                notes='入社時付与'
            )
            db.session.add(leave_credit)

        db.session.commit()
        print("✓ 3名のサンプル従業員を作成しました")
    else:
        print("\n✓ テスト企業は既に存在します")

    print("\n" + "="*50)
    print("データベース初期化が完了しました！")
    print("="*50)
    print("\nログイン情報:")
    print("\n【SaaS管理者】")
    print("  URL: /login")
    print("  メール: saas@example.com")
    print("  パスワード: saasadmin123")
    print("\n【企業管理者（テスト株式会社）】")
    print("  URL: /login")
    print("  メール: admin@test.com")
    print("  パスワード: admin123")
    print("="*50)
