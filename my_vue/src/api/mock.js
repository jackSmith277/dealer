// 模拟数据，用于开发阶段
export const mockData = {
  // 原始销量数据（10个月）
  originalSalesData: [
    { month: 1, original_sales: 120 },
    { month: 2, original_sales: 135 },
    { month: 3, original_sales: 142 },
    { month: 4, original_sales: 156 },
    { month: 5, original_sales: 168 },
    { month: 6, original_sales: 175 },
    { month: 7, original_sales: 182 },
    { month: 8, original_sales: 190 },
    { month: 9, original_sales: 198 },
    { month: 10, original_sales: 205 }
  ],

  // 经销商列表（这个暂时没有用）
  dealerList: ['A001', 'A002', 'A003', 'A004', 'A005'],

  // 预测结果示例
  predictionResult: {
    prediction: 180,
    sales_changes: [
      { month: 1, original_sales: 120 },
      { month: 2, original_sales: 135 },
      { month: 3, original_sales: 142 },
      { month: 4, original_sales: 156 },
      { month: 5, original_sales: 168 },
      { month: 6, original_sales: 175 },
      { month: 7, original_sales: 182 },
      { month: 8, original_sales: 190 },
      { month: 9, original_sales: 198 },
      { month: 10, original_sales: 205 }
    ],
    five_forces: {
      '传播获客力': 4.2,
      '体验力': 3.8,
      '转化力': 4.5,
      '服务力': 4.0,
      '经营力': 3.5,
      '综合得分': 4.2
    }
  }
}