from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256
import jwt
import datetime
import os
import pandas as pd
from dotenv import load_dotenv
from flask_migrate import Migrate

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/dealer_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化CORS和数据库
CORS(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 用户模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='dealer')
    status = db.Column(db.SmallInteger, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# 经销商模型
class Dealer(db.Model):
    __tablename__ = 'dealers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dealer_name = db.Column(db.String(100), nullable=False)
    dealer_type = db.Column(db.String(30), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    contact_name = db.Column(db.String(50), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# 预测历史记录模型
class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(20), nullable=False)
    dimension = db.Column(db.String(50), nullable=False)
    change_percentage = db.Column(db.Integer, nullable=False)
    base_year = db.Column(db.Integer, default=2024)
    base_month = db.Column(db.Integer, nullable=False)
    target_year = db.Column(db.Integer, default=2024)
    target_month = db.Column(db.Integer, nullable=False)
    predicted_sales = db.Column(db.Float, nullable=False)
    month_for_radar = db.Column(db.Integer, nullable=False)
    propagation_force = db.Column(db.Float, default=0)
    experience_force = db.Column(db.Float, default=0)
    conversion_force = db.Column(db.Float, default=0)
    service_force = db.Column(db.Float, default=0)
    operation_force = db.Column(db.Float, default=0)
    comprehensive_score = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# 分析报告模型
class AnalysisReport(db.Model):
    __tablename__ = 'analysis_report'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)  # 生成报告的用户名
    dealer_code = db.Column(db.String(20), nullable=False)
    report_date = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    selected_cards = db.Column(db.Text, nullable=False)  # JSON格式存储选中的卡片
    report_content = db.Column(db.Text, nullable=False)  # Markdown格式的报告内容

# 创建数据库表
with app.app_context():
    db.create_all()
    # 创建默认管理员账户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash='admin123',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

# 生成JWT令牌
def generate_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# 验证JWT令牌
def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except:
        return None

# 登录API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 401
    
    # 检查用户状态
    if user.status == 0:
        return jsonify({'error': '账号已禁用'}), 401
    
    # 暂时不加密，直接比较密码
    # if not pbkdf2_sha256.verify(password, user.password_hash):
    if password != user.password_hash:
        return jsonify({'error': '密码错误'}), 401
    
    token = generate_token(user)
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }
    })

# 注册API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'dealer')
    
    # 经销商注册时需要提供经销商信息
    dealer_data = data.get('dealer_data', {})
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    # 只有管理员可以创建管理员账户
    if role == 'admin':
        return jsonify({'error': '无权创建管理员账户'}), 403
    
    # 创建用户
    user = User(
        username=username,
        password_hash=password,  # 暂时不加密
        role=role
    )
    
    db.session.add(user)
    db.session.flush()  # 获取user.id但不提交
    
    # 如果是经销商，创建经销商信息
    if role == 'dealer' and dealer_data:
        dealer = Dealer(
            user_id=user.id,
            dealer_name=dealer_data.get('dealer_name'),
            dealer_type=dealer_data.get('dealer_type'),
            brand=dealer_data.get('brand'),
            level=dealer_data.get('level'),
            region=dealer_data.get('region'),
            contact_name=dealer_data.get('contact_name'),
            contact_phone=dealer_data.get('contact_phone'),
            address=dealer_data.get('address')
        )
        db.session.add(dealer)
    
    db.session.commit()
    
    return jsonify({'message': '注册成功'}), 201

# 获取用户列表API（仅管理员）
@app.route('/api/users', methods=['GET'])
def get_users():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供令牌'}), 401
    
    payload = verify_token(token.split(' ')[1] if ' ' in token else token)
    if not payload or payload['role'] != 'admin':
        return jsonify({'error': '无权限访问'}), 403
    
    users = User.query.all()
    user_list = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'status': user.status,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        }
        
        # 如果是经销商，添加经销商信息
        if user.role == 'dealer':
            dealer = Dealer.query.filter_by(user_id=user.id).first()
            if dealer:
                # 将 region 字段拆分成 province 和 city
                province = ''
                city = ''
                if dealer.region:
                    parts = dealer.region.split('/')
                    if len(parts) >= 2:
                        province = parts[0]
                        city = parts[1]
                    else:
                        province = dealer.region
                
                user_data['dealer'] = {
                    'id': dealer.id,
                    'dealer_name': dealer.dealer_name,
                    'dealer_type': dealer.dealer_type,
                    'brand': dealer.brand,
                    'level': dealer.level,
                    'region': dealer.region,
                    'province': province,
                    'city': city,
                    'contact_name': dealer.contact_name,
                    'contact_phone': dealer.contact_phone,
                    'address': dealer.address
                }
        
        user_list.append(user_data)
    
    return jsonify(user_list)

# 获取单个用户信息API（仅管理员）
@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未提供令牌'}), 401
        
        payload = verify_token(token.split(' ')[1] if ' ' in token else token)
        if not payload or payload['role'] != 'admin':
            return jsonify({'error': '无权限访问'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'status': user.status,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        }
        
        # 如果是经销商，添加经销商信息
        if user.role == 'dealer':
            dealer = Dealer.query.filter_by(user_id=user.id).first()
            if dealer:
                # 将 region 字段拆分成 province 和 city
                province = ''
                city = ''
                if dealer.region:
                    parts = dealer.region.split('/')
                    if len(parts) >= 2:
                        province = parts[0]
                        city = parts[1]
                    else:
                        province = dealer.region
                
                user_data['dealer'] = {
                    'id': dealer.id,
                    'dealer_name': dealer.dealer_name,
                    'dealer_type': dealer.dealer_type,
                    'brand': dealer.brand,
                    'level': dealer.level,
                    'region': dealer.region,
                    'province': province,
                    'city': city,
                    'contact_name': dealer.contact_name,
                    'contact_phone': dealer.contact_phone,
                    'address': dealer.address
                }
        
        return jsonify(user_data)
    except Exception as e:
        print(f'获取用户信息失败: {str(e)}')
        return jsonify({'error': f'获取失败: {str(e)}'}), 500

# 获取经销商信息API
@app.route('/api/dealers/<int:user_id>', methods=['GET'])
def get_dealer_info(user_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供令牌'}), 401
    
    payload = verify_token(token.split(' ')[1] if ' ' in token else token)
    if not payload:
        return jsonify({'error': '无效的令牌'}), 401
    
    # 检查权限：只有管理员或经销商本人可以访问
    if payload['role'] != 'admin' and payload['user_id'] != user_id:
        return jsonify({'error': '无权限访问'}), 403
    
    dealer = Dealer.query.filter_by(user_id=user_id).first()
    if not dealer:
        # 如果经销商信息不存在，返回空数据，允许用户填写
        return jsonify({
            'id': None,
            'user_id': user_id,
            'dealer_name': '',
            'dealer_type': '',
            'brand': '',
            'level': '',
            'province': '',
            'city': '',
            'contact_name': '',
            'contact_phone': '',
            'address': '',
            'created_at': None,
            'updated_at': None
        })
    
    # 将 region 字段拆分成 province 和 city
    province = ''
    city = ''
    if dealer.region:
        parts = dealer.region.split('/')
        if len(parts) >= 2:
            province = parts[0]
            city = parts[1]
        else:
            province = dealer.region
    
    return jsonify({
        'id': dealer.id,
        'user_id': dealer.user_id,
        'dealer_name': dealer.dealer_name,
        'dealer_type': dealer.dealer_type,
        'brand': dealer.brand,
        'level': dealer.level,
        'province': province,
        'city': city,
        'contact_name': dealer.contact_name,
        'contact_phone': dealer.contact_phone,
        'address': dealer.address,
        'created_at': dealer.created_at,
        'updated_at': dealer.updated_at
    })

# 更新经销商信息API
@app.route('/api/dealers/<int:user_id>', methods=['PUT'])
def update_dealer_info(user_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': '未提供令牌'}), 401
    
    payload = verify_token(token.split(' ')[1] if ' ' in token else token)
    if not payload:
        return jsonify({'error': '无效的令牌'}), 401
    
    # 检查权限：只有管理员或经销商本人可以修改
    if payload['role'] != 'admin' and payload['user_id'] != user_id:
        return jsonify({'error': '无权限修改'}), 403
    
    data = request.get_json()
    dealer = Dealer.query.filter_by(user_id=user_id).first()
    
    if not dealer:
        # 如果经销商信息不存在，创建新的经销商信息
        # 处理 province 和 city，拼接成 region
        region = ''
        if 'province' in data and 'city' in data:
            province = data.get('province', '')
            city = data.get('city', '')
            region = f"{province}{city}" if province and city else (province or city or '')
        else:
            region = data.get('region', '')
        
        dealer = Dealer(
            user_id=user_id,
            dealer_name=data.get('dealer_name', ''),
            dealer_type=data.get('dealer_type', ''),
            brand=data.get('brand', ''),
            level=data.get('level', ''),
            region=region,
            contact_name=data.get('contact_name', ''),
            contact_phone=data.get('contact_phone', ''),
            address=data.get('address', '')
        )
        db.session.add(dealer)
        db.session.commit()
        return jsonify({'message': '经销商信息创建成功'}), 201
    
    # 更新经销商信息
    if 'dealer_name' in data:
        dealer.dealer_name = data['dealer_name']
    if 'dealer_type' in data:
        dealer.dealer_type = data['dealer_type']
    if 'brand' in data:
        dealer.brand = data['brand']
    if 'level' in data:
        dealer.level = data['level']
    
    # 处理 province 和 city，拼接成 region
    if 'province' in data or 'city' in data:
        province = data.get('province', '')
        city = data.get('city', '')
        dealer.region = f"{province}{city}" if province and city else (province or city or '')
    elif 'region' in data:
        dealer.region = data['region']
    
    if 'contact_name' in data:
        dealer.contact_name = data['contact_name']
    if 'contact_phone' in data:
        dealer.contact_phone = data['contact_phone']
    if 'address' in data:
        dealer.address = data['address']
    
    db.session.commit()
    
    return jsonify({'message': '经销商信息更新成功'}), 200

# 更新用户信息API
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未提供令牌'}), 401
        
        payload = verify_token(token.split(' ')[1] if ' ' in token else token)
        if not payload:
            return jsonify({'error': '无效的令牌'}), 401
        
        # 检查权限：管理员可以修改所有用户，用户只能修改自己的密码
        if payload['role'] != 'admin' and payload['user_id'] != user_id:
            return jsonify({'error': '无权限访问'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 不能修改管理员账户，除非是管理员自己
        if user.role == 'admin' and payload['role'] != 'admin':
            return jsonify({'error': '不能修改管理员账户'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 更新用户信息
        # 非管理员只能更新自己的密码
        if payload['role'] != 'admin':
            if 'password' in data:
                user.password_hash = data['password']  # 暂时不加密
        else:
            # 管理员可以更新所有信息
            if 'password' in data:
                user.password_hash = data['password']  # 暂时不加密
            if 'status' in data:
                user.status = data['status']
        
        db.session.commit()
        return jsonify({'message': '用户信息更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'更新用户信息失败: {str(e)}')
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

# 删除用户API（仅管理员）
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未提供令牌'}), 401
        
        payload = verify_token(token.split(' ')[1] if ' ' in token else token)
        if not payload or payload['role'] != 'admin':
            return jsonify({'error': '无权限访问'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 不能删除管理员账户
        if user.role == 'admin':
            return jsonify({'error': '不能删除管理员账户'}), 403
        
        # 删除关联的经销商信息
        dealer = Dealer.query.filter_by(user_id=user_id).first()
        if dealer:
            db.session.delete(dealer)
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': '用户删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        print(f'删除用户失败: {str(e)}')
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

# 获取历史预测记录列表API
@app.route('/api/prediction/history', methods=['GET'])
def get_prediction_history():
    try:
        histories = PredictionHistory.query.order_by(PredictionHistory.created_at.desc()).all()
        
        history_list = []
        for history in histories:
            history_list.append({
                'id': history.id,
                'dealer_code': history.dealer_code,
                'dimension': history.dimension,
                'change_percentage': history.change_percentage,
                'base_year': history.base_year,
                'base_month': history.base_month,
                'target_year': history.target_year,
                'target_month': history.target_month,
                'predicted_sales': history.predicted_sales,
                'month_for_radar': history.month_for_radar,
                'propagation_force': history.propagation_force,
                'experience_force': history.experience_force,
                'conversion_force': history.conversion_force,
                'service_force': history.service_force,
                'operation_force': history.operation_force,
                'comprehensive_score': history.comprehensive_score,
                'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'data': history_list
        }), 200
        
    except Exception as e:
        print(f'获取历史记录失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

# 获取历史预测记录详情API
@app.route('/api/prediction/history/<int:id>', methods=['GET'])
def get_prediction_history_detail(id):
    try:
        history = PredictionHistory.query.get(id)
        if not history:
            return jsonify({'success': False, 'message': '历史记录不存在'}), 404
        
        result = {
            'id': history.id,
            'dealer_code': history.dealer_code,
            'dimension': history.dimension,
            'change_percentage': history.change_percentage,
            'base_year': history.base_year,
            'base_month': history.base_month,
            'target_year': history.target_year,
            'target_month': history.target_month,
            'predicted_sales': history.predicted_sales,
            'month_for_radar': history.month_for_radar,
            'propagation_force': history.propagation_force,
            'experience_force': history.experience_force,
            'conversion_force': history.conversion_force,
            'service_force': history.service_force,
            'operation_force': history.operation_force,
            'comprehensive_score': history.comprehensive_score,
            'created_at': history.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        print(f'获取历史记录详情失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

# 保存预测历史记录API
@app.route('/api/prediction/history', methods=['POST'])
def save_prediction_history():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        print('接收到的保存历史记录数据:', data)
        
        history = PredictionHistory(
            dealer_code=data.get('dealer_code'),
            dimension=data.get('dimension'),
            change_percentage=data.get('change_percentage'),
            base_year=data.get('base_year', 2024),
            base_month=data.get('base_month'),
            target_year=data.get('target_year', 2024),
            target_month=data.get('target_month'),
            predicted_sales=data.get('predicted_sales'),
            month_for_radar=data.get('month_for_radar'),
            propagation_force=data.get('propagation_force', 0),
            experience_force=data.get('experience_force', 0),
            conversion_force=data.get('conversion_force', 0),
            service_force=data.get('service_force', 0),
            operation_force=data.get('operation_force', 0),
            comprehensive_score=data.get('comprehensive_score', 0)
        )
        
        db.session.add(history)
        db.session.commit()
        
        print('历史记录保存成功:', history.id)
        
        return jsonify({
            'success': True,
            'message': '历史记录保存成功',
            'data': {
                'id': history.id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'保存历史记录失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

# 添加经销商API（仅管理员）
@app.route('/api/dealers', methods=['POST'])
def add_dealer():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未提供令牌'}), 401
        
        payload = verify_token(token.split(' ')[1] if ' ' in token else token)
        if not payload or payload['role'] != 'admin':
            return jsonify({'error': '无权限访问'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 检查必填字段
        required_fields = ['username', 'password', 'dealer_name', 'dealer_type', 'brand', 'level', 'contact_name', 'contact_phone', 'address']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field}不能为空'}), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        # 处理 province 和 city，拼接成 region
        region = ''
        if 'province' in data and 'city' in data:
            province = data.get('province', '')
            city = data.get('city', '')
            region = f"{province}{city}" if province and city else (province or city or '')
        else:
            region = data.get('region', '')
        
        # 创建用户
        user = User(
            username=data['username'],
            password_hash=data['password'],  # 暂时不加密
            role='dealer'
        )
        
        db.session.add(user)
        db.session.flush()  # 获取user.id
        
        # 创建经销商信息
        dealer = Dealer(
            user_id=user.id,
            dealer_name=data['dealer_name'],
            dealer_type=data['dealer_type'],
            brand=data['brand'],
            level=data['level'],
            region=region,
            contact_name=data['contact_name'],
            contact_phone=data['contact_phone'],
            address=data['address']
        )
        
        db.session.add(dealer)
        db.session.commit()
        
        return jsonify({'message': '经销商添加成功'}), 201
    except Exception as e:
        db.session.rollback()
        print(f'添加经销商失败: {str(e)}')
        return jsonify({'error': f'添加失败: {str(e)}'}), 500

# 获取政策数据API
@app.route('/api/policies', methods=['GET'])
def get_policies():
    try:
        excel_path = '地方促消费政策列表-202410-未整理.xlsx'
        
        if not os.path.exists(excel_path):
            return jsonify({'error': '政策数据文件不存在'}), 404
        
        df = pd.read_excel(excel_path)
        
        policies = []
        for _, row in df.iterrows():
            policy = {}
            for col in df.columns:
                policy[col] = str(row[col]) if pd.notna(row[col]) else ''
            policies.append(policy)
        
        return jsonify(policies), 200
    except Exception as e:
        print(f'获取政策数据失败: {str(e)}')
        return jsonify({'error': f'获取失败: {str(e)}'}), 500

@app.route('/api/comments', methods=['GET'])
def get_comments():
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '试驾评价.csv')
        
        df = None
        encodings = ['gbk', 'utf-8', 'gb2312', 'gb18030', 'utf-8-sig']
        last_error = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_path, encoding=encoding)
                print(f'成功使用 {encoding} 编码读取CSV文件')
                break
            except Exception as enc_err:
                last_error = enc_err
                continue
        
        if df is None:
            print(f'所有编码方式都失败，最后错误: {str(last_error)}')
            return jsonify({'error': f'读取CSV文件失败: {str(last_error)}'}), 500
        
        comments = []
        if '评价内容' in df.columns and '综合得分' in df.columns:
            for idx, row in df.iterrows():
                content = row.get('评价内容')
                score = row.get('综合得分')
                
                if pd.notna(content) and str(content).strip():
                    score_value = float(score) if pd.notna(score) else 3.0
                    
                    if score_value > 3:
                        sentiment = 'positive'
                    elif score_value < 3:
                        sentiment = 'negative'
                    else:
                        sentiment = 'neutral'
                    
                    comments.append({
                        'content': str(content).strip(),
                        'score': score_value,
                        'sentiment': sentiment
                    })
        
        print(f'成功读取 {len(comments)} 条评价')
        return jsonify(comments), 200
    except Exception as e:
        print(f'获取试驾评价失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'获取失败: {str(e)}'}), 500

# 保存分析报告API
@app.route('/api/analysis-reports', methods=['POST'])
def save_analysis_report():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        print('接收到的保存分析报告数据:', data)
        
        # 创建分析报告记录
        report = AnalysisReport(
            username=data.get('username'),
            dealer_code=data.get('dealer_code'),
            selected_cards=data.get('selected_cards'),  # JSON字符串
            report_content=data.get('report_content')
        )
        
        db.session.add(report)
        db.session.commit()
        
        print('分析报告保存成功:', report.id)
        
        return jsonify({
            'success': True,
            'message': '分析报告保存成功',
            'data': {
                'id': report.id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'保存分析报告失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

# 获取分析报告列表API
@app.route('/api/analysis-reports', methods=['GET'])
def get_analysis_reports():
    try:
        username = request.args.get('username')
        
        # 构建查询
        query = AnalysisReport.query
        if username:
            query = query.filter_by(username=username)
        
        # 按报告生成日期倒序排列
        reports = query.order_by(AnalysisReport.report_date.desc()).all()
        
        # 格式化结果
        report_list = []
        for report in reports:
            report_list.append({
                'id': report.id,
                'username': report.username,
                'dealer_code': report.dealer_code,
                'report_date': report.report_date.strftime('%Y-%m-%d %H:%M:%S'),
                'selected_cards': report.selected_cards,
                'report_content': report.report_content
            })
        
        return jsonify({
            'success': True,
            'data': report_list
        }), 200
        
    except Exception as e:
        print(f'获取分析报告列表失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

# 获取分析报告详情API
@app.route('/api/analysis-reports/<int:id>', methods=['GET'])
def get_analysis_report_detail(id):
    try:
        report = AnalysisReport.query.get(id)
        if not report:
            return jsonify({'success': False, 'message': '分析报告不存在'}), 404
        
        result = {
            'id': report.id,
            'username': report.username,
            'dealer_code': report.dealer_code,
            'report_date': report.report_date.strftime('%Y-%m-%d %H:%M:%S'),
            'selected_cards': report.selected_cards,
            'report_content': report.report_content
        }
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        print(f'获取分析报告详情失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

# 删除分析报告API
@app.route('/api/analysis-reports/<int:id>', methods=['DELETE'])
def delete_analysis_report(id):
    try:
        report = AnalysisReport.query.get(id)
        if not report:
            return jsonify({'success': False, 'message': '分析报告不存在'}), 404
        
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '分析报告删除成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f'删除分析报告失败: {str(e)}')
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

from wordcloud_service import wordcloud_generator

@app.route('/api/wordcloud', methods=['POST'])
def generate_wordcloud():
    try:
        data = request.get_json()
        comments = data.get('comments', [])
        positive_words = data.get('positiveWords', [])
        negative_words = data.get('negativeWords', [])
        neutral_words = data.get('neutralWords', [])
        wordcloud_type = data.get('type', 'all')
        
        if wordcloud_type == 'circular':
            image_base64 = wordcloud_generator.generate_circular_wordcloud(
                positive_words, negative_words, neutral_words,
                width=900, height=600
            )
        else:
            filtered_comments = comments
            if wordcloud_type == 'positive':
                filtered_comments = [c for c in comments if c.get('sentiment') == 'positive']
            elif wordcloud_type == 'negative':
                filtered_comments = [c for c in comments if c.get('sentiment') == 'negative']
            elif wordcloud_type == 'neutral':
                filtered_comments = [c for c in comments if c.get('sentiment') == 'neutral']
            
            image_base64 = wordcloud_generator.generate_wordcloud_for_sentiment(
                filtered_comments, wordcloud_type, width=900, height=550
            )
        
        if image_base64:
            return jsonify({
                'success': True,
                'image': image_base64
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '无法生成词云，数据不足'
            }), 400
            
    except Exception as e:
        print(f'生成词云失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500

if __name__ == '__main__':
    print('Starting Flask server...')
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f'Error starting server: {e}')
        import traceback
        traceback.print_exc()