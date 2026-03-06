/**
 * 数据提取工具
 * 从图表和卡片中提取数据用于生成报告
 */

/**
 * 从 DealerDashboard 组件中提取选中卡片的数据
 * @param {object} vm - Vue 组件实例
 * @param {array} selectedCards - 选中的卡片ID列表
 * @returns {object} - 提取的数据对象
 */
export function extractCardData(vm, selectedCards) {
  const cardData = {};

  console.log('开始提取数据，选中的卡片:', selectedCards);

  selectedCards.forEach(cardId => {
    console.log('处理卡片:', cardId);
    switch (cardId) {
      case 'trend':
        cardData.trend = extractTrendData(vm);
        console.log('提取 trend 数据:', cardData.trend);
        break;
      case 'funnel':
        cardData.funnel = extractFunnelData(vm);
        console.log('提取 funnel 数据:', cardData.funnel);
        break;
      case 'snapshot':
        cardData.snapshot = extractSnapshotData(vm);
        console.log('提取 snapshot 数据:', cardData.snapshot);
        break;
      case 'metrics':
        cardData.metrics = extractMetricsData(vm);
        console.log('提取 metrics 数据:', cardData.metrics);
        break;
      case 'rate':
        cardData.rate = extractRateData(vm);
        console.log('提取 rate 数据:', cardData.rate);
        break;
      case 'responseTime':
        cardData.responseTime = extractResponseTimeData(vm);
        console.log('提取 responseTime 数据:', cardData.responseTime);
        break;
      case 'gsev':
        cardData.gsev = extractGsevData(vm);
        console.log('提取 gsev 数据:', cardData.gsev);
        break;
      case 'policy':
        cardData.policy = extractPolicyData(vm);
        console.log('提取 policy 数据:', cardData.policy);
        break;
      case 'review':
        cardData.review = extractReviewData(vm);
        console.log('提取 review 数据:', cardData.review);
        break;
      // 兼容旧的ID
      case 'conversion':
        cardData.conversion = extractConversionData(vm);
        break;
      case 'testDrive':
        cardData.testDrive = extractTestDriveData(vm);
        break;
      case 'customerFlow':
        cardData.customerFlow = extractCustomerFlowData(vm);
        break;
      case 'defeatRate':
        cardData.defeatRate = extractDefeatRateData(vm);
        break;
      case 'fiveForces':
        cardData.fiveForces = extractFiveForcesData(vm);
        break;
      default:
        console.warn('未知的卡片ID:', cardId);
    }
  });

  console.log('数据提取完成，总共提取了', Object.keys(cardData).length, '个卡片的数据');
  return cardData;
}

/**
 * 提取趋势数据
 */
function extractTrendData(vm) {
  // 使用真实的月份数据
  const months = vm.filteredMonths || vm.months || [];
  
  // 使用 getSeries 方法获取真实数据 - 四个维度
  const salesData = vm.getSeries ? vm.getSeries('销量').map(v => parseFloat(v.toFixed(2))) : [];
  const trafficData = vm.getSeries ? vm.getSeries('客流量').map(v => parseFloat(v.toFixed(2))) : [];
  const leadsData = vm.getSeries ? vm.getSeries('线索量').map(v => parseFloat(v.toFixed(2))) : [];
  const potentialData = vm.getSeries ? vm.getSeries('潜客量').map(v => parseFloat(v.toFixed(2))) : [];
  
  console.log('提取趋势数据 - 月份:', months);
  console.log('提取趋势数据 - 销量:', salesData);
  console.log('提取趋势数据 - 客流量:', trafficData);
  console.log('提取趋势数据 - 线索:', leadsData);
  console.log('提取趋势数据 - 潜客:', potentialData);
  
  return {
    months: months,
    sales: salesData,
    traffic: trafficData,
    leads: leadsData,
    potential: potentialData
  };
}

/**
 * 提取漏斗数据
 */
function extractFunnelData(vm) {
  // 从真实数据计算漏斗各阶段的数据
  const leadsData = vm.getSeries ? vm.getSeries('线索量') : [];
  const potentialData = vm.getSeries ? vm.getSeries('潜客量') : [];
  const salesData = vm.getSeries ? vm.getSeries('销量') : [];
  const trafficData = vm.getSeries ? vm.getSeries('客流量') : [];
  
  // 计算平均值（均值）而不是总和
  const avgLeads = leadsData.length > 0 
    ? parseFloat((leadsData.reduce((sum, val) => sum + val, 0) / leadsData.length).toFixed(2))
    : 0;
  const avgPotential = potentialData.length > 0 
    ? parseFloat((potentialData.reduce((sum, val) => sum + val, 0) / potentialData.length).toFixed(2))
    : 0;
  const avgSales = salesData.length > 0 
    ? parseFloat((salesData.reduce((sum, val) => sum + val, 0) / salesData.length).toFixed(2))
    : 0;
  const avgTraffic = trafficData.length > 0 
    ? parseFloat((trafficData.reduce((sum, val) => sum + val, 0) / trafficData.length).toFixed(2))
    : 0;
  
  // 计算转化率（基于平均值）
  const leadConversionRate = avgLeads > 0 ? parseFloat(((avgPotential / avgLeads) * 100).toFixed(2)) : 0;
  const storeRate = avgPotential > 0 ? parseFloat(((avgTraffic / avgPotential) * 100).toFixed(2)) : 0;
  const salesRate = avgTraffic > 0 ? parseFloat(((avgSales / avgTraffic) * 100).toFixed(2)) : 0;
  
  console.log('提取漏斗数据 - 线索均值:', avgLeads);
  console.log('提取漏斗数据 - 潜客均值:', avgPotential);
  console.log('提取漏斗数据 - 进店均值:', avgTraffic);
  console.log('提取漏斗数据 - 成交均值:', avgSales);
  console.log('提取漏斗数据 - 线索转化率:', leadConversionRate);
  console.log('提取漏斗数据 - 进店率:', storeRate);
  console.log('提取漏斗数据 - 成交率:', salesRate);
  
  return {
    leads: avgLeads,  // 均值，保留两位小数
    potential: avgPotential,  // 均值，保留两位小数
    store: avgTraffic,  // 均值，保留两位小数
    sales: avgSales,  // 均值，保留两位小数
    leadConversionRate: leadConversionRate,  // 保留两位小数
    storeRate: storeRate,  // 保留两位小数
    salesRate: salesRate  // 保留两位小数
  };
}

/**
 * 提取月度快照数据
 */
function extractSnapshotData(vm) {
  // 使用真实的 monthSnapshots computed 属性
  const snapshots = vm.monthSnapshots || [];
  
  console.log('提取快照数据 - 快照数量:', snapshots.length);
  
  return {
    count: snapshots.length,
    data: snapshots.map(snap => ({
      month: snap.month,
      sales: snap.sales,
      traffic: snap.traffic,
      leads: snap.leads,
      potential: snap.potential,
      rate: snap.rate
    }))
  };
}

/**
 * 提取核心指标数据
 */
function extractMetricsData(vm) {
  // 从真实数据计算核心指标
  const salesData = vm.getSeries ? vm.getSeries('销量') : [];
  const trafficData = vm.getSeries ? vm.getSeries('客流量') : [];
  const leadsData = vm.getSeries ? vm.getSeries('线索量') : [];
  const potentialData = vm.getSeries ? vm.getSeries('潜客量') : [];
  const rateData = vm.getSeries ? vm.getSeries('成交率') : [];
  
  const totalSales = parseFloat(salesData.reduce((sum, val) => sum + val, 0).toFixed(2));
  const totalTraffic = parseFloat(trafficData.reduce((sum, val) => sum + val, 0).toFixed(2));
  const totalLeads = parseFloat(leadsData.reduce((sum, val) => sum + val, 0).toFixed(2));
  const totalPotential = parseFloat(potentialData.reduce((sum, val) => sum + val, 0).toFixed(2));
  const avgConversionRate = rateData.length > 0 
    ? parseFloat((rateData.reduce((sum, val) => sum + val, 0) / rateData.length * 100).toFixed(2))
    : 0;
  
  console.log('提取核心指标 - 总销量:', totalSales);
  console.log('提取核心指标 - 总客流:', totalTraffic);
  
  return {
    totalSales: totalSales,  // 保留两位小数
    totalTraffic: totalTraffic,  // 保留两位小数
    totalLeads: totalLeads,  // 保留两位小数
    totalPotential: totalPotential,  // 保留两位小数
    avgConversionRate: avgConversionRate  // 保留两位小数
  };
}

/**
 * 提取转化率数据
 */
function extractConversionData(vm) {
  // 从真实数据计算转化率
  const leadsData = vm.getSeries ? vm.getSeries('线索量') : [];
  const potentialData = vm.getSeries ? vm.getSeries('潜客量') : [];
  const trafficData = vm.getSeries ? vm.getSeries('客流量') : [];
  const salesData = vm.getSeries ? vm.getSeries('销量') : [];
  
  const totalLeads = leadsData.reduce((sum, val) => sum + val, 0);
  const totalPotential = potentialData.reduce((sum, val) => sum + val, 0);
  const totalTraffic = trafficData.reduce((sum, val) => sum + val, 0);
  const totalSales = salesData.reduce((sum, val) => sum + val, 0);
  
  const leadToPotential = totalLeads > 0 ? parseFloat(((totalPotential / totalLeads) * 100).toFixed(2)) : 0;
  const potentialToStore = totalPotential > 0 ? parseFloat(((totalTraffic / totalPotential) * 100).toFixed(2)) : 0;
  const storeToSales = totalTraffic > 0 ? parseFloat(((totalSales / totalTraffic) * 100).toFixed(2)) : 0;
  const overall = totalLeads > 0 ? parseFloat(((totalSales / totalLeads) * 100).toFixed(2)) : 0;
  
  return {
    leadToPotential: leadToPotential,
    potentialToStore: potentialToStore,
    storeToSales: storeToSales,
    overall: overall
  };
}

/**
 * 提取成交率/战败率数据
 */
function extractRateData(vm) {
  // 获取真实的成交率和战败率数据
  const months = vm.filteredMonths || vm.months || [];
  const successRateData = vm.getSeries ? vm.getSeries('成交率').map(v => parseFloat((v * 100).toFixed(2))) : [];
  const defeatRateData = vm.getSeries ? vm.getSeries('战败率').map(v => parseFloat((v * 100).toFixed(2))) : [];
  
  const avgSuccessRate = successRateData.length > 0 
    ? parseFloat((successRateData.reduce((sum, val) => sum + val, 0) / successRateData.length).toFixed(2))
    : 0;
  const avgDefeatRate = defeatRateData.length > 0
    ? parseFloat((defeatRateData.reduce((sum, val) => sum + val, 0) / defeatRateData.length).toFixed(2))
    : 0;
  
  console.log('提取成交率数据 - 月度成交率:', successRateData);
  console.log('提取战败率数据 - 月度战败率:', defeatRateData);
  
  return {
    months: months,
    successRate: successRateData,
    defeatRate: defeatRateData,
    avgSuccessRate: avgSuccessRate,
    avgDefeatRate: avgDefeatRate
  };
}

/**
 * 提取GSEV数据
 */
function extractGsevData(vm) {
  // 获取真实的GSEV数据
  const months = vm.filteredMonths || vm.months || [];
  const gsevData = vm.getSeries ? vm.getSeries('GSEV').map(v => parseFloat(v.toFixed(2))) : [];
  
  const avgGsev = gsevData.length > 0
    ? parseFloat((gsevData.reduce((sum, val) => sum + val, 0) / gsevData.length).toFixed(2))
    : 0;
  
  // 判断趋势
  let trend = '稳定';
  if (gsevData.length >= 2) {
    const firstHalf = gsevData.slice(0, Math.floor(gsevData.length / 2));
    const secondHalf = gsevData.slice(Math.floor(gsevData.length / 2));
    const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;
    
    if (secondAvg > firstAvg * 1.05) trend = '上升';
    else if (secondAvg < firstAvg * 0.95) trend = '下降';
  }
  
  console.log('提取GSEV数据 - 月度GSEV:', gsevData);
  
  return {
    months: months,
    gsevValues: gsevData,
    avgGsev: avgGsev,
    trend: trend
  };
}

/**
 * 提取评价数据
 */
function extractReviewData(vm) {
  // 获取真实的评价数据
  const months = vm.filteredMonths || vm.months || [];
  const totalReviewsData = vm.getSeries ? vm.getSeries('评价数').map(v => parseFloat(v.toFixed(2))) : [];
  const goodReviewsData = vm.getSeries ? vm.getSeries('好评数').map(v => parseFloat(v.toFixed(2))) : [];
  const badReviewsData = vm.getSeries ? vm.getSeries('差评数').map(v => parseFloat(v.toFixed(2))) : [];
  
  const totalReviews = parseFloat(totalReviewsData.reduce((sum, val) => sum + val, 0).toFixed(2));
  const totalGood = parseFloat(goodReviewsData.reduce((sum, val) => sum + val, 0).toFixed(2));
  const totalBad = parseFloat(badReviewsData.reduce((sum, val) => sum + val, 0).toFixed(2));
  
  const goodRate = totalReviews > 0 ? parseFloat(((totalGood / totalReviews) * 100).toFixed(2)) : 0;
  const badRate = totalReviews > 0 ? parseFloat(((totalBad / totalReviews) * 100).toFixed(2)) : 0;
  
  console.log('提取评价数据 - 总评价数:', totalReviews);
  console.log('提取评价数据 - 好评率:', goodRate + '%');
  
  return {
    months: months,
    totalReviews: totalReviewsData,
    goodReviews: goodReviewsData,
    badReviews: badReviewsData,
    totalCount: totalReviews,  // 保留两位小数
    totalGoodCount: totalGood,  // 保留两位小数
    totalBadCount: totalBad,  // 保留两位小数
    goodRate: goodRate,
    badRate: badRate
  };
}

/**
 * 提取响应时间数据
 */
function extractResponseTimeData(vm) {
  // 获取真实的响应时间数据
  const successResponseData = vm.getSeries ? vm.getSeries('成交响应时间') : [];
  const defeatResponseData = vm.getSeries ? vm.getSeries('战败响应时间') : [];
  
  const avgSuccess = successResponseData.length > 0
    ? (successResponseData.reduce((sum, val) => sum + val, 0) / successResponseData.length).toFixed(2)
    : 0;
  const avgDefeat = defeatResponseData.length > 0
    ? (defeatResponseData.reduce((sum, val) => sum + val, 0) / defeatResponseData.length).toFixed(2)
    : 0;
  const avgTotal = successResponseData.length > 0 && defeatResponseData.length > 0
    ? ((parseFloat(avgSuccess) + parseFloat(avgDefeat)) / 2).toFixed(2)
    : 0;
  
  console.log('提取响应时间 - 成交响应时间:', successResponseData);
  console.log('提取响应时间 - 战败响应时间:', defeatResponseData);
  
  return {
    success: parseFloat(avgSuccess),
    defeat: parseFloat(avgDefeat),
    average: parseFloat(avgTotal),
    monthlySuccess: successResponseData,
    monthlyDefeat: defeatResponseData
  };
}

/**
 * 提取试驾数据
 */
function extractTestDriveData(vm) {
  return {
    total: vm.testDriveTotal || 500,
    sales: vm.testDriveSales || 200,
    conversionRate: vm.testDriveConversionRate || 40
  };
}

/**
 * 提取客流量数据
 */
function extractCustomerFlowData(vm) {
  return {
    monthly: vm.customerFlowMonthly || [800, 850, 780, 920, 880, 950, 900, 870, 910, 940],
    average: vm.customerFlowAverage || 880,
    trend: vm.customerFlowTrend || '稳定增长'
  };
}

/**
 * 提取战败率数据
 */
function extractDefeatRateData(vm) {
  return {
    rate: vm.defeatRate || 35,
    reasons: vm.defeatReasons || ['价格因素', '竞品对比', '服务体验', '其他']
  };
}

/**
 * 提取政策数据
 */
function extractPolicyData(vm) {
  // 获取真实的政策数据
  const policyData = vm.getSeries ? vm.getSeries('政策').map(v => parseFloat(v.toFixed(2))) : [];
  const months = vm.filteredMonths || vm.months || [];
  
  // 统计政策数量
  const totalPolicies = parseFloat(policyData.reduce((sum, val) => sum + val, 0).toFixed(2));
  const avgPolicies = policyData.length > 0 
    ? parseFloat((totalPolicies / policyData.length).toFixed(2))
    : 0;
  
  // 判断政策影响（基于政策数量趋势）
  let impact = '中性';
  if (policyData.length >= 2) {
    const firstHalf = policyData.slice(0, Math.floor(policyData.length / 2));
    const secondHalf = policyData.slice(Math.floor(policyData.length / 2));
    const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;
    
    if (secondAvg > firstAvg * 1.2) impact = '积极增强';
    else if (secondAvg > firstAvg) impact = '积极';
    else if (secondAvg < firstAvg * 0.8) impact = '减弱';
  }
  
  console.log('提取政策数据 - 月度政策数:', policyData);
  console.log('提取政策数据 - 总政策数:', totalPolicies);
  
  return {
    months: months,
    monthlyCount: policyData,
    totalCount: totalPolicies,  // 保留两位小数
    avgCount: avgPolicies,  // 保留两位小数
    impact: impact
  };
}

/**
 * 提取五力模型数据
 */
function extractFiveForcesData(vm) {
  return {
    propagation: vm.propagationForce || 15,
    experience: vm.experienceForce || 16,
    conversion: vm.conversionForce || 32,
    service: vm.serviceForce || 8,
    operation: vm.operationForce || 7,
    total: vm.totalScore || 78
  };
}

/**
 * 格式化报告数据为可读文本
 * @param {object} cardData - 卡片数据
 * @returns {string} - 格式化的文本
 */
export function formatReportData(cardData) {
  let text = '# 销售数据分析报告\n\n';
  text += `生成时间: ${new Date().toLocaleString('zh-CN')}\n\n`;
  text += '---\n\n';

  if (cardData.trend) {
    text += '## 销量/线索/潜客月度走势\n\n';
    text += `- 销量趋势: ${cardData.trend.sales.join(', ')}\n`;
    text += `- 线索趋势: ${cardData.trend.leads.join(', ')}\n`;
    text += `- 潜客趋势: ${cardData.trend.potential.join(', ')}\n\n`;
  }

  if (cardData.funnel) {
    text += '## 销售漏斗模型\n\n';
    text += `| 阶段 | 数量 | 转化率 |\n`;
    text += `|------|------|--------|\n`;
    text += `| 线索 | ${cardData.funnel.leads} | - |\n`;
    text += `| 潜客 | ${cardData.funnel.potential} | ${cardData.funnel.leadConversionRate}% |\n`;
    text += `| 进店 | ${cardData.funnel.store} | ${cardData.funnel.storeRate}% |\n`;
    text += `| 成交 | ${cardData.funnel.sales} | ${cardData.funnel.salesRate}% |\n\n`;
  }

  if (cardData.conversion) {
    text += '## 转化率分析\n\n';
    text += `- 线索转潜客率: ${cardData.conversion.leadToPotential}%\n`;
    text += `- 潜客进店率: ${cardData.conversion.potentialToStore}%\n`;
    text += `- 进店成交率: ${cardData.conversion.storeToSales}%\n`;
    text += `- 整体转化率: ${cardData.conversion.overall}%\n\n`;
  }

  if (cardData.fiveForces) {
    text += '## 五力模型评分\n\n';
    text += `- 传播获客力: ${cardData.fiveForces.propagation}/20\n`;
    text += `- 体验力: ${cardData.fiveForces.experience}/20\n`;
    text += `- 转化力: ${cardData.fiveForces.conversion}/40\n`;
    text += `- 服务力: ${cardData.fiveForces.service}/10\n`;
    text += `- 经营力: ${cardData.fiveForces.operation}/10\n`;
    text += `- **综合得分: ${cardData.fiveForces.total}/100**\n\n`;
  }

  return text;
}
