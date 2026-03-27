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
from wordcloud_service import wordcloud_generator
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
            predicted_sales=data.get('predicted_sales')
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


class MonthlyMetrics11d(db.Model):
    __tablename__ = 'monthly_metrics_11d'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(50), nullable=False)
    stat_year = db.Column(db.Integer, nullable=False)
    stat_month = db.Column(db.Integer, nullable=False)
    sales = db.Column(db.Numeric(18, 4), nullable=True)
    potential_customers = db.Column(db.Numeric(18, 4), nullable=True)
    test_drives = db.Column(db.Numeric(18, 4), nullable=True)
    leads = db.Column(db.Numeric(18, 4), nullable=True)
    customer_flow = db.Column(db.Numeric(18, 4), nullable=True)
    defeat_rate = db.Column(db.Numeric(18, 6), nullable=True)
    success_rate = db.Column(db.Numeric(18, 6), nullable=True)
    success_response_time = db.Column(db.Numeric(18, 4), nullable=True)
    defeat_response_time = db.Column(db.Numeric(18, 4), nullable=True)
    policy = db.Column(db.Numeric(18, 4), nullable=True)
    gsev = db.Column(db.Numeric(18, 4), nullable=True)


class MonthlyRadarScores(db.Model):
    __tablename__ = 'monthly_radar_scores'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(50), nullable=False)
    stat_year = db.Column(db.Integer, nullable=False)
    stat_month = db.Column(db.Integer, nullable=False)
    spread_force = db.Column(db.Numeric(18, 4), nullable=True)
    experience_force = db.Column(db.Numeric(18, 4), nullable=True)
    conversion_force = db.Column(db.Numeric(18, 4), nullable=True)
    service_force = db.Column(db.Numeric(18, 4), nullable=True)
    operation_force = db.Column(db.Numeric(18, 4), nullable=True)


@app.route('/api/dealers/list', methods=['GET'])
def get_dealers_list():
    try:
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2]}
        except:
            pass
        
        dealers = []
        for dealer_code, info in dealer_info_map.items():
            dealers.append({
                'dealer_code': dealer_code,
                'province': info.get('province', ''),
                'city': info.get('city', '')
            })
        
        return jsonify({
            'success': True,
            'dealers': dealers
        }), 200
        
    except Exception as e:
        print(f'获取经销商列表失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    try:
        year = request.args.get('year', type=int)
        dealer_code = request.args.get('dealer_code', type=str)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        evaluation_map = {}
        if year == 2024:
            try:
                eval_result = db.session.execute(db.text("""
                    SELECT dealer_code, 
                           evaluation_score_m01, evaluation_score_m02, evaluation_score_m03,
                           evaluation_score_m04, evaluation_score_m05, evaluation_score_m06,
                           evaluation_score_m07, evaluation_score_m08, evaluation_score_m09,
                           evaluation_score_m10
                    FROM radar_source_2024
                """))
                for row in eval_result:
                    evaluation_map[row[0]] = {
                        1: float(row[1]) if row[1] else None,
                        2: float(row[2]) if row[2] else None,
                        3: float(row[3]) if row[3] else None,
                        4: float(row[4]) if row[4] else None,
                        5: float(row[5]) if row[5] else None,
                        6: float(row[6]) if row[6] else None,
                        7: float(row[7]) if row[7] else None,
                        8: float(row[8]) if row[8] else None,
                        9: float(row[9]) if row[9] else None,
                        10: float(row[10]) if row[10] else None,
                    }
            except:
                pass
        
        query = MonthlyMetrics11d.query
        if year:
            query = query.filter(MonthlyMetrics11d.stat_year == year)
        if dealer_code:
            query = query.filter(MonthlyMetrics11d.dealer_code == dealer_code)
        
        records = query.order_by(MonthlyMetrics11d.dealer_code, MonthlyMetrics11d.stat_year, MonthlyMetrics11d.stat_month).all()
        
        dealer_data_map = {}
        for record in records:
            dc = record.dealer_code
            if dc not in dealer_data_map:
                info = dealer_info_map.get(dc, {'province': '', 'fed_level': ''})
                dealer_data_map[dc] = {
                    '经销商代码': dc,
                    '省份': info['province'],
                    '销售FED级别': info['fed_level']
                }
            
            month = record.stat_month
            dealer_data_map[dc][f'{month}月销量'] = float(record.sales) if record.sales else None
            dealer_data_map[dc][f'{month}月客流量'] = float(record.customer_flow) if record.customer_flow else None
            dealer_data_map[dc][f'{month}月潜客量'] = float(record.potential_customers) if record.potential_customers else None
            dealer_data_map[dc][f'{month}月线索量'] = float(record.leads) if record.leads else None
            dealer_data_map[dc][f'{month}月成交率'] = float(record.success_rate) if record.success_rate else None
            dealer_data_map[dc][f'{month}月战败率'] = float(record.defeat_rate) if record.defeat_rate else None
            dealer_data_map[dc][f'{month}月成交响应时间'] = float(record.success_response_time) if record.success_response_time else None
            dealer_data_map[dc][f'{month}月战败响应时间'] = float(record.defeat_response_time) if record.defeat_response_time else None
            dealer_data_map[dc][f'{month}月政策'] = float(record.policy) if record.policy else None
            dealer_data_map[dc][f'{month}月GSEV'] = float(record.gsev) if record.gsev else None
            dealer_data_map[dc][f'{month}月试驾数'] = float(record.test_drives) if record.test_drives else None
            
            if dc in evaluation_map and month in evaluation_map[dc]:
                eval_score = evaluation_map[dc][month]
                dealer_data_map[dc][f'{month}月评价分'] = eval_score
                if eval_score:
                    good_percent = (eval_score / 5.0) * 100
                    bad_percent = 100 - good_percent
                    dealer_data_map[dc][f'{month}月好评率'] = round(good_percent, 1)
                    dealer_data_map[dc][f'{month}月差评率'] = round(bad_percent, 1)
        
        return jsonify({
            'success': True,
            'data': list(dealer_data_map.values())
        }), 200
        
    except Exception as e:
        print(f'获取仪表盘数据失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/dashboard/years', methods=['GET'])
def get_available_years():
    try:
        years = db.session.query(MonthlyMetrics11d.stat_year).distinct().order_by(MonthlyMetrics11d.stat_year).all()
        year_list = [y[0] for y in years]
        return jsonify({
            'success': True,
            'data': year_list
        }), 200
    except Exception as e:
        print(f'获取可用年份失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/five-forces/radar', methods=['GET'])
def get_five_forces_radar():
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        dealer_code = request.args.get('dealer_code', type=str)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        query = MonthlyRadarScores.query
        if year:
            query = query.filter(MonthlyRadarScores.stat_year == year)
        if month:
            query = query.filter(MonthlyRadarScores.stat_month == month)
        if dealer_code:
            query = query.filter(MonthlyRadarScores.dealer_code == dealer_code)
        
        records = query.order_by(MonthlyRadarScores.dealer_code, MonthlyRadarScores.stat_year, MonthlyRadarScores.stat_month).all()
        
        result = []
        for record in records:
            info = dealer_info_map.get(record.dealer_code, {'province': '', 'fed_level': ''})
            result.append({
                '经销商代码': record.dealer_code,
                '省份': info['province'],
                '年份': record.stat_year,
                '月份': record.stat_month,
                '传播获客力': float(record.spread_force) if record.spread_force else None,
                '体验力': float(record.experience_force) if record.experience_force else None,
                '转化力': float(record.conversion_force) if record.conversion_force else None,
                '服务力': float(record.service_force) if record.service_force else None,
                '经营力': float(record.operation_force) if record.operation_force else None
            })
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        print(f'获取五力雷达数据失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/five-forces/years', methods=['GET'])
def get_radar_available_years():
    try:
        years = db.session.query(MonthlyRadarScores.stat_year).distinct().order_by(MonthlyRadarScores.stat_year).all()
        year_list = [y[0] for y in years]
        return jsonify({
            'success': True,
            'data': year_list
        }), 200
    except Exception as e:
        print(f'获取可用年份失败: {str(e)}')
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/overview', methods=['GET'])
def get_index_overview():
    try:
        year = request.args.get('year', type=int, default=2024)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        avg_spread = sum(float(r.spread_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_experience = sum(float(r.experience_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_conversion = sum(float(r.conversion_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_service = sum(float(r.service_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_operation = sum(float(r.operation_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        
        radar_avg = {
            '传播获客力': round(avg_spread, 2),
            '体验力': round(avg_experience, 2),
            '转化力': round(avg_conversion, 2),
            '服务力': round(avg_service, 2),
            '经营力': round(avg_operation, 2)
        }
        
        metrics_query = MonthlyMetrics11d.query.filter(MonthlyMetrics11d.stat_year == year)
        metrics_records = metrics_query.all()
        
        monthly_avg = {}
        for month in range(1, 13):
            month_records = [r for r in metrics_records if r.stat_month == month]
            if month_records:
                monthly_avg[month] = {
                    '销量': round(sum(float(r.sales or 0) for r in month_records) / len(month_records), 0),
                    '客流量': round(sum(float(r.customer_flow or 0) for r in month_records) / len(month_records), 0),
                    '线索量': round(sum(float(r.leads or 0) for r in month_records) / len(month_records), 0),
                    '潜客量': round(sum(float(r.potential_customers or 0) for r in month_records) / len(month_records), 0)
                }
        
        ranking_data = []
        dealer_all_scores = {}
        for r in radar_records:
            dc = r.dealer_code
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            if dc not in dealer_all_scores:
                dealer_all_scores[dc] = []
            dealer_all_scores[dc].append(total)
        
        dealer_scores = {}
        for dc, scores in dealer_all_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            dealer_scores[dc] = {
                'code': dc,
                'province': dealer_info_map.get(dc, {}).get('province', ''),
                'totalScore': round(avg_score, 2)
            }
        
        ranking_data = sorted(dealer_scores.values(), key=lambda x: x['totalScore'], reverse=True)
        
        warning_red = sorted([d for d in dealer_scores.values() if d['totalScore'] < 3], key=lambda x: x['totalScore'])
        warning_orange = sorted([d for d in dealer_scores.values() if 3 <= d['totalScore'] < 4], key=lambda x: x['totalScore'])
        warning_green = sorted([d for d in dealer_scores.values() if d['totalScore'] >= 4], key=lambda x: -x['totalScore'])
        
        province_count = {}
        city_count = {}
        for dc, info in dealer_info_map.items():
            province = info.get('province', '')
            city = info.get('city', '')
            if province:
                province_count[province] = province_count.get(province, 0) + 1
            if city:
                city_count[city] = city_count.get(city, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'radar_avg': radar_avg,
                'monthly_avg': monthly_avg,
                'warning': {
                    'red': warning_red,
                    'orange': warning_orange,
                    'green': warning_green
                },
                'province_count': province_count,
                'city_count': city_count,
                'total_dealers': len(dealer_info_map)
            }
        }), 200
        
    except Exception as e:
        print(f'获取概览数据失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/ranking', methods=['GET'])
def get_ranking():
    try:
        year = request.args.get('year', type=int, default=2024)
        sort_by = request.args.get('sort_by', type=str, default='total')
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        dealer_scores = {}
        for r in radar_records:
            dc = r.dealer_code
            if dc not in dealer_scores:
                dealer_scores[dc] = {
                    'spread': [],
                    'experience': [],
                    'conversion': [],
                    'service': [],
                    'operation': [],
                    'total': []
                }
            
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            
            dealer_scores[dc]['spread'].append(float(r.spread_force or 0))
            dealer_scores[dc]['experience'].append(float(r.experience_force or 0))
            dealer_scores[dc]['conversion'].append(float(r.conversion_force or 0))
            dealer_scores[dc]['service'].append(float(r.service_force or 0))
            dealer_scores[dc]['operation'].append(float(r.operation_force or 0))
            dealer_scores[dc]['total'].append(total)
        
        ranking_data = []
        for dc, scores in dealer_scores.items():
            avg_spread = sum(scores['spread']) / len(scores['spread']) if scores['spread'] else 0
            avg_experience = sum(scores['experience']) / len(scores['experience']) if scores['experience'] else 0
            avg_conversion = sum(scores['conversion']) / len(scores['conversion']) if scores['conversion'] else 0
            avg_service = sum(scores['service']) / len(scores['service']) if scores['service'] else 0
            avg_operation = sum(scores['operation']) / len(scores['operation']) if scores['operation'] else 0
            avg_total = sum(scores['total']) / len(scores['total']) if scores['total'] else 0
            
            score_map = {
                'total': avg_total,
                'spread': avg_spread,
                'experience': avg_experience,
                'conversion': avg_conversion,
                'service': avg_service,
                'operation': avg_operation
            }
            
            ranking_data.append({
                'code': dc,
                'province': dealer_info_map.get(dc, {}).get('province', ''),
                'score': round(score_map.get(sort_by, avg_total), 2)
            })
        
        ranking_data = sorted(ranking_data, key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': ranking_data
        }), 200
        
    except Exception as e:
        print(f'获取排名数据失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/province-stores', methods=['GET'])
def get_province_stores():
    try:
        year = request.args.get('year', type=int, default=2024)
        province = request.args.get('province', type=str)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        dealer_scores = {}
        for r in radar_records:
            dc = r.dealer_code
            if dc not in dealer_scores:
                total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
                dealer_scores[dc] = {
                    'code': dc,
                    'province': dealer_info_map.get(dc, {}).get('province', ''),
                    'city': dealer_info_map.get(dc, {}).get('city', ''),
                    'totalScore': round(total, 2)
                }
        
        metrics_records = MonthlyMetrics11d.query.filter(MonthlyMetrics11d.stat_year == year).all()
        dealer_sales = {}
        for r in metrics_records:
            dc = r.dealer_code
            if dc not in dealer_sales:
                dealer_sales[dc] = 0
            dealer_sales[dc] += float(r.sales or 0)
        
        stores = []
        for dc, info in dealer_scores.items():
            if province and info['province'] != province:
                continue
            stores.append({
                'id': dc,
                'name': dc,
                'province': info['province'],
                'city': info['city'],
                'totalScore': info['totalScore'],
                'sales': int(dealer_sales.get(dc, 0))
            })
        
        return jsonify({
            'success': True,
            'data': stores
        }), 200
        
    except Exception as e:
        print(f'获取省份门店数据失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


PROVINCE_REGION_MAP = {
    '辽宁省': '东北',
    '山东省': '华东',
    '湖北省': '华中',
    '广东省': '华南',
    '广西壮族自治区': '华南'
}


@app.route('/api/index/header-kpi', methods=['GET'])
def get_header_kpi():
    try:
        year = request.args.get('year', type=int, default=2024)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        dealer_all_scores = {}
        for r in radar_records:
            dc = r.dealer_code
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            if dc not in dealer_all_scores:
                dealer_all_scores[dc] = []
            dealer_all_scores[dc].append(total)
        
        dealer_scores = {}
        for dc, scores in dealer_all_scores.items():
            dealer_scores[dc] = sum(scores) / len(scores) if scores else 0
        
        total_dealers = len(dealer_info_map)
        avg_score = round(sum(dealer_scores.values()) / len(dealer_scores), 2) if dealer_scores else 0
        
        warning_count = len([s for s in dealer_scores.values() if s < 3])
        
        prev_year = year - 1
        prev_radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == prev_year)
        prev_radar_records = prev_radar_query.all()
        prev_dealer_all_scores = {}
        for r in prev_radar_records:
            dc = r.dealer_code
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            if dc not in prev_dealer_all_scores:
                prev_dealer_all_scores[dc] = []
            prev_dealer_all_scores[dc].append(total)
        
        prev_dealer_scores = {}
        for dc, scores in prev_dealer_all_scores.items():
            prev_dealer_scores[dc] = sum(scores) / len(scores) if scores else 0
        
        prev_avg_score = sum(prev_dealer_scores.values()) / len(prev_dealer_scores) if prev_dealer_scores else avg_score
        score_change = round(avg_score - prev_avg_score, 2)
        score_change_pct = round((score_change / prev_avg_score * 100), 1) if prev_avg_score > 0 else 0
        
        prev_warning_count = len([s for s in prev_dealer_scores.values() if s < 3])
        warning_change = warning_count - prev_warning_count
        
        province_avg_scores = {}
        for dc, score in dealer_scores.items():
            province = dealer_info_map.get(dc, {}).get('province', '')
            if province:
                if province not in province_avg_scores:
                    province_avg_scores[province] = []
                province_avg_scores[province].append(score)
        
        top_province = ''
        top_province_score = 0
        for province, scores in province_avg_scores.items():
            avg = sum(scores) / len(scores)
            if avg > top_province_score:
                top_province_score = avg
                top_province = province
        
        active_dealers = total_dealers - warning_count
        
        return jsonify({
            'success': True,
            'data': {
                'totalDealers': total_dealers,
                'avgScore': avg_score,
                'warningCount': warning_count,
                'topProvince': top_province,
                'topProvinceScore': round(top_province_score, 2),
                'activeDealers': active_dealers,
                'activeRatio': round(active_dealers / total_dealers * 100, 1) if total_dealers > 0 else 0
            }
        }), 200
        
    except Exception as e:
        print(f'获取头部KPI失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/region-dashboard', methods=['GET'])
def get_region_dashboard():
    try:
        year = request.args.get('year', type=int, default=2024)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        region_data = {}
        for r in radar_records:
            dc = r.dealer_code
            province = dealer_info_map.get(dc, {}).get('province', '')
            region = PROVINCE_REGION_MAP.get(province, '其他')
            
            if region not in region_data:
                region_data[region] = {
                    'dealers': set(),
                    'dealer_scores': {},
                    'provinces': set(),
                    'spread_forces': [],
                    'experience_forces': [],
                    'conversion_forces': [],
                    'service_forces': [],
                    'operation_forces': []
                }
            
            region_data[region]['dealers'].add(dc)
            region_data[region]['provinces'].add(province)
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            if dc not in region_data[region]['dealer_scores']:
                region_data[region]['dealer_scores'][dc] = []
            region_data[region]['dealer_scores'][dc].append(total)
            region_data[region]['spread_forces'].append(float(r.spread_force or 0))
            region_data[region]['experience_forces'].append(float(r.experience_force or 0))
            region_data[region]['conversion_forces'].append(float(r.conversion_force or 0))
            region_data[region]['service_forces'].append(float(r.service_force or 0))
            region_data[region]['operation_forces'].append(float(r.operation_force or 0))
        
        prev_year = year - 1
        prev_radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == prev_year)
        prev_radar_records = prev_radar_query.all()
        
        prev_region_data = {}
        for r in prev_radar_records:
            dc = r.dealer_code
            province = dealer_info_map.get(dc, {}).get('province', '')
            region = PROVINCE_REGION_MAP.get(province, '其他')
            
            if region not in prev_region_data:
                prev_region_data[region] = {'scores': []}
            
            total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
            prev_region_data[region]['scores'].append(total)
        
        force_names = {
            'spread': '传播获客力',
            'experience': '体验力',
            'conversion': '转化力',
            'service': '服务力',
            'operation': '经营力'
        }
        
        region_list = []
        for region, data in region_data.items():
            dealer_count = len(data['dealers'])
            
            dealer_avg_scores = {}
            for dc, scores in data['dealer_scores'].items():
                dealer_avg_scores[dc] = sum(scores) / len(scores) if scores else 0
            
            avg_score = round(sum(dealer_avg_scores.values()) / len(dealer_avg_scores), 2) if dealer_avg_scores else 0
            
            warning_count = len([s for s in dealer_avg_scores.values() if s < 3])
            
            avg_spread = sum(data['spread_forces']) / len(data['spread_forces']) if data['spread_forces'] else 0
            avg_experience = sum(data['experience_forces']) / len(data['experience_forces']) if data['experience_forces'] else 0
            avg_conversion = sum(data['conversion_forces']) / len(data['conversion_forces']) if data['conversion_forces'] else 0
            avg_service = sum(data['service_forces']) / len(data['service_forces']) if data['service_forces'] else 0
            avg_operation = sum(data['operation_forces']) / len(data['operation_forces']) if data['operation_forces'] else 0
            
            forces = {
                'spread': avg_spread,
                'experience': avg_experience,
                'conversion': avg_conversion,
                'service': avg_service,
                'operation': avg_operation
            }
            top_force = max(forces, key=forces.get)
            bottom_force = min(forces, key=forces.get)
            top_score = forces[top_force]
            bottom_score = forces[bottom_force]
            
            if avg_score >= 4:
                insight = f'综合表现优秀，{force_names[top_force]}达{top_score:.2f}分，建议保持并推广成功经验'
            elif avg_score >= 3:
                insight = f'{force_names[top_force]}表现较好({top_score:.2f}分)，建议重点提升{force_names[bottom_force]}({bottom_score:.2f}分)'
            else:
                insight = f'整体评分偏低，{force_names[bottom_force]}({bottom_score:.2f}分)急需改善，建议全面诊断'
            
            region_list.append({
                'region': region,
                'dealer_count': dealer_count,
                'avg_score': avg_score,
                'warning_count': warning_count,
                'provinces': list(data['provinces']),
                'insight': insight,
                'top_force': force_names[top_force],
                'bottom_force': force_names[bottom_force]
            })
        
        region_list.sort(key=lambda x: x['avg_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': region_list
        }), 200
        
    except Exception as e:
        print(f'获取区域业绩看板失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/metrics-comparison', methods=['GET'])
def get_metrics_comparison():
    try:
        year = request.args.get('year', type=int, default=2024)
        month = request.args.get('month', type=int, default=10)
        
        metrics_records = MonthlyMetrics11d.query.filter(
            MonthlyMetrics11d.stat_year == year,
            MonthlyMetrics11d.stat_month == month
        ).all()
        
        total_sales = sum(float(r.sales or 0) for r in metrics_records)
        total_flow = sum(float(r.customer_flow or 0) for r in metrics_records)
        total_leads = sum(float(r.leads or 0) for r in metrics_records)
        total_potential = sum(float(r.potential_customers or 0) for r in metrics_records)
        
        sales_list = [float(r.sales or 0) for r in metrics_records if r.sales]
        flow_list = [float(r.customer_flow or 0) for r in metrics_records if r.customer_flow]
        leads_list = [float(r.leads or 0) for r in metrics_records if r.leads]
        potential_list = [float(r.potential_customers or 0) for r in metrics_records if r.potential_customers]
        
        return jsonify({
            'success': True,
            'data': {
                'sales': {
                    'total': int(total_sales),
                    'max': int(max(sales_list)) if sales_list else 0,
                    'min': int(min(sales_list)) if sales_list else 0,
                    'avg': int(sum(sales_list) / len(sales_list)) if sales_list else 0
                },
                'flow': {
                    'total': int(total_flow),
                    'max': int(max(flow_list)) if flow_list else 0,
                    'min': int(min(flow_list)) if flow_list else 0,
                    'avg': int(sum(flow_list) / len(flow_list)) if flow_list else 0
                },
                'leads': {
                    'total': int(total_leads),
                    'max': int(max(leads_list)) if leads_list else 0,
                    'min': int(min(leads_list)) if leads_list else 0,
                    'avg': int(sum(leads_list) / len(leads_list)) if leads_list else 0
                },
                'potential': {
                    'total': int(total_potential),
                    'max': int(max(potential_list)) if potential_list else 0,
                    'min': int(min(potential_list)) if potential_list else 0,
                    'avg': int(sum(potential_list) / len(potential_list)) if potential_list else 0
                }
            }
        }), 200
        
    except Exception as e:
        print(f'获取核心指标对比失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/insights', methods=['GET'])
def get_insights():
    try:
        year = request.args.get('year', type=int, default=2024)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        radar_query = MonthlyRadarScores.query.filter(MonthlyRadarScores.stat_year == year)
        radar_records = radar_query.all()
        
        dealer_scores = {}
        dealer_forces = {}
        for r in radar_records:
            dc = r.dealer_code
            if dc not in dealer_scores:
                total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
                dealer_scores[dc] = total
                dealer_forces[dc] = {
                    'spread': float(r.spread_force or 0),
                    'experience': float(r.experience_force or 0),
                    'conversion': float(r.conversion_force or 0),
                    'service': float(r.service_force or 0),
                    'operation': float(r.operation_force or 0)
                }
        
        region_scores = {}
        for dc, score in dealer_scores.items():
            province = dealer_info_map.get(dc, {}).get('province', '')
            region = PROVINCE_REGION_MAP.get(province, '其他')
            if region not in region_scores:
                region_scores[region] = []
            region_scores[region].append(score)
        
        region_avg = {r: sum(s)/len(s) for r, s in region_scores.items()}
        top_region = max(region_avg, key=region_avg.get) if region_avg else ''
        bottom_region = min(region_avg, key=region_avg.get) if region_avg else ''
        
        avg_forces = {
            'spread': sum(f['spread'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0,
            'experience': sum(f['experience'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0,
            'conversion': sum(f['conversion'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0,
            'service': sum(f['service'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0,
            'operation': sum(f['operation'] for f in dealer_forces.values()) / len(dealer_forces) if dealer_forces else 0
        }
        top_force = max(avg_forces, key=avg_forces.get)
        bottom_force = min(avg_forces, key=avg_forces.get)
        
        force_names = {
            'spread': '传播获客力',
            'experience': '体验力',
            'conversion': '转化力',
            'service': '服务力',
            'operation': '经营力'
        }
        
        warning_dealers = [dc for dc, score in dealer_scores.items() if score < 15]
        warning_provinces = {}
        for dc in warning_dealers:
            province = dealer_info_map.get(dc, {}).get('province', '')
            if province:
                warning_provinces[province] = warning_provinces.get(province, 0) + 1
        
        top_warning_province = max(warning_provinces, key=warning_provinces.get) if warning_provinces else ''
        
        insights = []
        
        if top_region:
            insights.append({
                'type': 'highlight',
                'icon': '💡',
                'content': f'{top_region}区域表现优异，平均评分{region_avg[top_region]:.2f}分，建议其他区域参考其运营经验'
            })
        
        if bottom_region and bottom_region != top_region:
            insights.append({
                'type': 'warning',
                'icon': '⚠️',
                'content': f'{bottom_region}区域评分相对较低（{region_avg[bottom_region]:.2f}分），建议加强培训和运营支持'
            })
        
        insights.append({
            'type': 'trend',
            'icon': '📈',
            'content': f'全国五力分析中，{force_names[top_force]}表现最佳，{force_names[bottom_force]}有待提升'
        })
        
        if top_warning_province:
            insights.append({
                'type': 'suggestion',
                'icon': '🎯',
                'content': f'{top_warning_province}预警门店数最多（{warning_provinces[top_warning_province]}家），建议重点关注'
            })
        
        return jsonify({
            'success': True,
            'data': insights
        }), 200
        
    except Exception as e:
        print(f'获取数据洞察失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@app.route('/api/index/area-data', methods=['GET'])
def get_area_data():
    try:
        year = request.args.get('year', type=int, default=2024)
        province = request.args.get('province', default='')
        city = request.args.get('city', default='')
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province, city, fed_level FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = {'province': row[1], 'city': row[2], 'fed_level': row[3]}
        except:
            pass
        
        if city:
            target_dealers = [dc for dc, info in dealer_info_map.items() if info.get('city') == city]
        elif province:
            target_dealers = [dc for dc, info in dealer_info_map.items() if info.get('province') == province]
        else:
            target_dealers = list(dealer_info_map.keys())
        
        radar_query = MonthlyRadarScores.query.filter(
            MonthlyRadarScores.stat_year == year,
            MonthlyRadarScores.dealer_code.in_(target_dealers)
        )
        radar_records = radar_query.all()
        
        avg_spread = sum(float(r.spread_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_experience = sum(float(r.experience_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_conversion = sum(float(r.conversion_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_service = sum(float(r.service_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        avg_operation = sum(float(r.operation_force or 0) for r in radar_records) / len(radar_records) if radar_records else 0
        
        radar_avg = {
            '传播获客力': round(avg_spread, 2),
            '体验力': round(avg_experience, 2),
            '转化力': round(avg_conversion, 2),
            '服务力': round(avg_service, 2),
            '经营力': round(avg_operation, 2)
        }
        
        metrics_query = MonthlyMetrics11d.query.filter(
            MonthlyMetrics11d.stat_year == year,
            MonthlyMetrics11d.dealer_code.in_(target_dealers)
        )
        metrics_records = metrics_query.all()
        
        monthly_avg = {}
        for month in range(1, 13):
            month_records = [r for r in metrics_records if r.stat_month == month]
            if month_records:
                monthly_avg[month] = {
                    '销量': round(sum(float(r.sales or 0) for r in month_records) / len(month_records), 0),
                    '客流量': round(sum(float(r.customer_flow or 0) for r in month_records) / len(month_records), 0),
                    '线索量': round(sum(float(r.leads or 0) for r in month_records) / len(month_records), 0),
                    '潜客量': round(sum(float(r.potential_customers or 0) for r in month_records) / len(month_records), 0)
                }
        
        dealer_scores = {}
        for r in radar_records:
            dc = r.dealer_code
            if dc not in dealer_scores:
                total = float(r.spread_force or 0) * 0.2 + float(r.experience_force or 0) * 0.2 + float(r.conversion_force or 0) * 0.4 + float(r.service_force or 0) * 0.1 + float(r.operation_force or 0) * 0.1
                dealer_scores[dc] = {
                    'code': dc,
                    'province': dealer_info_map.get(dc, {}).get('province', ''),
                    'city': dealer_info_map.get(dc, {}).get('city', ''),
                    'totalScore': round(total, 2)
                }
        
        ranking_data = sorted(dealer_scores.values(), key=lambda x: x['totalScore'], reverse=True)
        
        warning_red = sorted([d for d in dealer_scores.values() if d['totalScore'] < 3], key=lambda x: x['totalScore'])
        warning_orange = sorted([d for d in dealer_scores.values() if 3 <= d['totalScore'] < 4], key=lambda x: x['totalScore'])
        warning_green = sorted([d for d in dealer_scores.values() if d['totalScore'] >= 4], key=lambda x: -x['totalScore'])
        
        pie_data = [
            {'name': '高风险 (总分<3)', 'value': len(warning_red)},
            {'name': '中风险 (3≤总分<4)', 'value': len(warning_orange)},
            {'name': '健康 (总分≥4)', 'value': len(warning_green)}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'radar_avg': radar_avg,
                'monthly_avg': monthly_avg,
                'ranking': ranking_data,
                'warning': {
                    'red': warning_red,
                    'orange': warning_orange,
                    'green': warning_green
                },
                'pie_data': pie_data,
                'dealer_count': len(target_dealers)
            }
        }), 200
        
    except Exception as e:
        print(f'获取区域数据失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

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

@app.route('/api/radar/data', methods=['GET'])
def get_radar_data():
    try:
        year = request.args.get('year', type=int, default=2024)
        month = request.args.get('month', type=int, default=1)
        
        dealer_info_map = {}
        try:
            dealer_info_result = db.session.execute(db.text("SELECT dealer_code, province FROM v_dealer_info"))
            for row in dealer_info_result:
                dealer_info_map[row[0]] = row[1]
        except:
            pass
        
        query = MonthlyRadarScores.query.filter(
            MonthlyRadarScores.stat_year == year,
            MonthlyRadarScores.stat_month == month
        )
        records = query.all()
        
        data = []
        for record in records:
            data.append({
                'dealer_code': record.dealer_code,
                'province': dealer_info_map.get(record.dealer_code, ''),
                'spread_force': float(record.spread_force) if record.spread_force else 0,
                'experience_force': float(record.experience_force) if record.experience_force else 0,
                'conversion_force': float(record.conversion_force) if record.conversion_force else 0,
                'service_force': float(record.service_force) if record.service_force else 0,
                'operation_force': float(record.operation_force) if record.operation_force else 0
            })
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
        
    except Exception as e:
        print(f'获取雷达数据失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500

if __name__ == '__main__':
    print('Starting Flask server...')
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f'Error starting server: {e}')
        import traceback
        traceback.print_exc()