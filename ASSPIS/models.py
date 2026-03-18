"""
ASSPIS 数据库模型定义
包含3张核心表：
1. monthly_metrics_11d - 11维月度基础数据
2. radar_source_2024 - 雷达图输入源数据
3. monthly_radar_scores - 五力结果数据
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class MonthlyMetrics11d(db.Model):
    __tablename__ = 'monthly_metrics_11d'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(50), nullable=False, comment='经销商代码')
    stat_year = db.Column(db.Integer, nullable=False, comment='年')
    stat_month = db.Column(db.Integer, nullable=False, comment='月')
    sales = db.Column(db.Numeric(18, 4), nullable=True, comment='销量')
    potential_customers = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量')
    test_drives = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数')
    leads = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量')
    customer_flow = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量')
    defeat_rate = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率')
    success_rate = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率')
    success_response_time = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间')
    defeat_response_time = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间')
    policy = db.Column(db.Numeric(18, 4), nullable=True, comment='政策')
    gsev = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV')
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, comment='导入时间')
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        db.UniqueConstraint('dealer_code', 'stat_year', 'stat_month', name='uq_dealer_year_month'),
        db.CheckConstraint('stat_month >= 1 AND stat_month <= 12', name='ck_stat_month_range'),
        db.Index('idx_dealer_code', 'dealer_code'),
        db.Index('idx_year_month', 'stat_year', 'stat_month'),
    )

    def to_dict(self):
        return {
            'dealer_code': self.dealer_code,
            'stat_year': self.stat_year,
            'stat_month': self.stat_month,
            'sales': float(self.sales) if self.sales else None,
            'potential_customers': float(self.potential_customers) if self.potential_customers else None,
            'test_drives': float(self.test_drives) if self.test_drives else None,
            'leads': float(self.leads) if self.leads else None,
            'customer_flow': float(self.customer_flow) if self.customer_flow else None,
            'defeat_rate': float(self.defeat_rate) if self.defeat_rate else None,
            'success_rate': float(self.success_rate) if self.success_rate else None,
            'success_response_time': float(self.success_response_time) if self.success_response_time else None,
            'defeat_response_time': float(self.defeat_response_time) if self.defeat_response_time else None,
            'policy': float(self.policy) if self.policy else None,
            'gsev': float(self.gsev) if self.gsev else None,
        }


class RadarSource2024(db.Model):
    __tablename__ = 'radar_source_2024'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(50), nullable=False, unique=True, comment='经销商代码')
    province = db.Column(db.String(100), nullable=True, comment='省份')
    fed_level = db.Column(db.String(100), nullable=True, comment='销售FED级别')
    terminal_check_avg = db.Column(db.Numeric(18, 6), nullable=True, comment='终端检核平均分')

    customer_flow_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量1月')
    customer_flow_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量2月')
    customer_flow_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量3月')
    customer_flow_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量4月')
    customer_flow_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量5月')
    customer_flow_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量6月')
    customer_flow_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量7月')
    customer_flow_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量8月')
    customer_flow_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量9月')
    customer_flow_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='客流量10月')

    potential_customers_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量1月')
    potential_customers_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量2月')
    potential_customers_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量3月')
    potential_customers_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量4月')
    potential_customers_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量5月')
    potential_customers_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量6月')
    potential_customers_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量7月')
    potential_customers_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量8月')
    potential_customers_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量9月')
    potential_customers_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='潜客量10月')

    leads_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量1月')
    leads_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量2月')
    leads_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量3月')
    leads_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量4月')
    leads_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量5月')
    leads_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量6月')
    leads_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量7月')
    leads_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量8月')
    leads_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量9月')
    leads_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='线索量10月')

    success_rate_m01 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率1月')
    success_rate_m02 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率2月')
    success_rate_m03 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率3月')
    success_rate_m04 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率4月')
    success_rate_m05 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率5月')
    success_rate_m06 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率6月')
    success_rate_m07 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率7月')
    success_rate_m08 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率8月')
    success_rate_m09 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率9月')
    success_rate_m10 = db.Column(db.Numeric(18, 6), nullable=True, comment='成交率10月')

    defeat_rate_m01 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率1月')
    defeat_rate_m02 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率2月')
    defeat_rate_m03 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率3月')
    defeat_rate_m04 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率4月')
    defeat_rate_m05 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率5月')
    defeat_rate_m06 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率6月')
    defeat_rate_m07 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率7月')
    defeat_rate_m08 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率8月')
    defeat_rate_m09 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率9月')
    defeat_rate_m10 = db.Column(db.Numeric(18, 6), nullable=True, comment='战败率10月')

    sales_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量1月')
    sales_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量2月')
    sales_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量3月')
    sales_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量4月')
    sales_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量5月')
    sales_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量6月')
    sales_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量7月')
    sales_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量8月')
    sales_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量9月')
    sales_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='销量10月')

    success_response_time_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间1月')
    success_response_time_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间2月')
    success_response_time_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间3月')
    success_response_time_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间4月')
    success_response_time_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间5月')
    success_response_time_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间6月')
    success_response_time_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间7月')
    success_response_time_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间8月')
    success_response_time_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间9月')
    success_response_time_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='成交响应时间10月')

    defeat_response_time_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间1月')
    defeat_response_time_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间2月')
    defeat_response_time_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间3月')
    defeat_response_time_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间4月')
    defeat_response_time_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间5月')
    defeat_response_time_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间6月')
    defeat_response_time_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间7月')
    defeat_response_time_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间8月')
    defeat_response_time_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间9月')
    defeat_response_time_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='战败响应时间10月')

    test_drives_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数1月')
    test_drives_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数2月')
    test_drives_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数3月')
    test_drives_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数4月')
    test_drives_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数5月')
    test_drives_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数6月')
    test_drives_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数7月')
    test_drives_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数8月')
    test_drives_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数9月')
    test_drives_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='试驾数10月')

    policy_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策1月')
    policy_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策2月')
    policy_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策3月')
    policy_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策4月')
    policy_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策5月')
    policy_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策6月')
    policy_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策7月')
    policy_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策8月')
    policy_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策9月')
    policy_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='政策10月')

    gsev_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV1月')
    gsev_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV2月')
    gsev_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV3月')
    gsev_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV4月')
    gsev_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV5月')
    gsev_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV6月')
    gsev_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV7月')
    gsev_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV8月')
    gsev_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV9月')
    gsev_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='GSEV10月')

    evaluation_score_m01 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分1月')
    evaluation_score_m02 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分2月')
    evaluation_score_m03 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分3月')
    evaluation_score_m04 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分4月')
    evaluation_score_m05 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分5月')
    evaluation_score_m06 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分6月')
    evaluation_score_m07 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分7月')
    evaluation_score_m08 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分8月')
    evaluation_score_m09 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分9月')
    evaluation_score_m10 = db.Column(db.Numeric(18, 4), nullable=True, comment='评价分10月')

    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, comment='导入时间')
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        db.Index('idx_radar_dealer_code', 'dealer_code'),
    )


class MonthlyRadarScores(db.Model):
    __tablename__ = 'monthly_radar_scores'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dealer_code = db.Column(db.String(50), nullable=False, comment='经销商代码')
    stat_year = db.Column(db.Integer, nullable=False, comment='年')
    stat_month = db.Column(db.Integer, nullable=False, comment='月')
    spread_force = db.Column(db.Numeric(18, 4), nullable=True, comment='传播获客力')
    experience_force = db.Column(db.Numeric(18, 4), nullable=True, comment='体验力')
    conversion_force = db.Column(db.Numeric(18, 4), nullable=True, comment='转化力')
    service_force = db.Column(db.Numeric(18, 4), nullable=True, comment='服务力')
    operation_force = db.Column(db.Numeric(18, 4), nullable=True, comment='经营力')
    calc_version = db.Column(db.String(50), nullable=True, comment='计算版本号')
    source_tag = db.Column(db.String(50), nullable=True, comment='数据来源标识')
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, comment='生成时间')
    updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    __table_args__ = (
        db.UniqueConstraint('dealer_code', 'stat_year', 'stat_month', name='uq_radar_dealer_year_month'),
        db.CheckConstraint('stat_month >= 1 AND stat_month <= 12', name='ck_radar_stat_month_range'),
        db.Index('idx_radar_scores_dealer_code', 'dealer_code'),
        db.Index('idx_radar_scores_year_month', 'stat_year', 'stat_month'),
    )

    def to_dict(self):
        return {
            'dealer_code': self.dealer_code,
            'stat_year': self.stat_year,
            'stat_month': self.stat_month,
            'spread_force': float(self.spread_force) if self.spread_force else None,
            'experience_force': float(self.experience_force) if self.experience_force else None,
            'conversion_force': float(self.conversion_force) if self.conversion_force else None,
            'service_force': float(self.service_force) if self.service_force else None,
            'operation_force': float(self.operation_force) if self.operation_force else None,
            'calc_version': self.calc_version,
            'source_tag': self.source_tag,
        }
