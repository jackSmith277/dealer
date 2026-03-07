/**
 * DeepSeek API 集成模块
 * 用于调用 DeepSeek API 生成智能分析报告
 */

// 这两个值放在环境变量里面了
//const DEEPSEEK_API_KEY = import.meta.env?.VITE_DEEPSEEK_API_KEY ;
//const DEEPSEEK_API_URL = import.meta.env?.VITE_DEEPSEEK_API_URL ;

const DEEPSEEK_API_KEY = 'sk-829e1bc28fe145beae4780d96fd5d2df'
const DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'



// 检查环境变量是否配置
if (!DEEPSEEK_API_KEY || DEEPSEEK_API_KEY === 'your_api_key_here' || DEEPSEEK_API_KEY === 'sk-your-api-key-here') {
  console.warn('⚠️ DeepSeek API Key 未配置或使用了示例值，请在 .env 文件中配置 VITE_DEEPSEEK_API_KEY');
}

if (!DEEPSEEK_API_URL) {
  console.warn('⚠️ DeepSeek API URL 未配置，请在 .env 文件中配置 VITE_DEEPSEEK_API_URL');
}

/**
 * 调用 DeepSeek API
 * @param {string} prompt - 提示词
 * @param {object} options - 可选配置
 * @returns {Promise<string>} - API 返回的文本
 */
export async function callDeepSeek(prompt, options = {}) {
  const {
    model = 'deepseek-chat',
    temperature = 0.7,
    maxTokens = 4000,
    stream = false
  } = options;

  try {
    const response = await fetch(DEEPSEEK_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
      },
      body: JSON.stringify({
        model: model,
        messages: [
          {
            role: 'system',
            content: '你是一位专业的汽车销售数据分析师，擅长分析经销商的销售数据、五力模型、市场趋势等，并提供专业的改进建议。'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: temperature,
        max_tokens: maxTokens,
        stream: stream
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`DeepSeek API 错误: ${errorData.error?.message || response.statusText}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;
  } catch (error) {
    console.error('DeepSeek API 调用失败:', error);
    throw error;
  }
}

/**
 * 生成销售数据分析报告
 * @param {object} cardData - 选中的卡片数据
 * @returns {Promise<string>} - 分析报告文本
 */
export async function generateSalesReport(cardData) {
  const prompt = buildSalesReportPrompt(cardData);
  return await callDeepSeek(prompt, {
    temperature: 0.7,
    maxTokens: 4000
  });
}

/**
 * 构建销售报告的提示词
 * @param {object} cardData - 卡片数据
 * @returns {string} - 提示词
 */
function buildSalesReportPrompt(cardData) {
  let prompt = `请基于以下汽车经销商的销售数据，生成一份专业的分析报告。报告应包含：
1. 数据概览
2. 关键指标分析
3. 趋势分析
4. 问题诊断
5. 改进建议

数据如下：

`;

  // 添加各个卡片的数据
  if (cardData.trend) {
    prompt += `## 销量/客流量/线索/潜客月度走势
- 销量数据: ${JSON.stringify(cardData.trend.sales)}
- 客流量数据: ${JSON.stringify(cardData.trend.traffic)}
- 线索数据: ${JSON.stringify(cardData.trend.leads)}
- 潜客数据: ${JSON.stringify(cardData.trend.potential)}

`;
  }

  if (cardData.funnel) {
    prompt += `## 销售漏斗模型
- 线索量: ${cardData.funnel.leads}
- 潜客量: ${cardData.funnel.potential}
- 进店量: ${cardData.funnel.store}
- 成交量: ${cardData.funnel.sales}
- 线索转化率: ${cardData.funnel.leadConversionRate}%
- 潜客进店率: ${cardData.funnel.storeRate}%
- 进店成交率: ${cardData.funnel.salesRate}%

`;
  }

  if (cardData.conversion) {
    prompt += `## 转化率分析
- 线索转潜客率: ${cardData.conversion.leadToPotential}%
- 潜客进店率: ${cardData.conversion.potentialToStore}%
- 进店成交率: ${cardData.conversion.storeToSales}%
- 整体转化率: ${cardData.conversion.overall}%

`;
  }

  if (cardData.responseTime) {
    prompt += `## 响应时间分析
- 成交响应时间: ${cardData.responseTime.success} 小时
- 战败响应时间: ${cardData.responseTime.defeat} 小时
- 平均响应时间: ${cardData.responseTime.average} 小时

`;
  }

  if (cardData.testDrive) {
    prompt += `## 试驾数据
- 试驾总数: ${cardData.testDrive.total}
- 试驾成交数: ${cardData.testDrive.sales}
- 试驾成交率: ${cardData.testDrive.conversionRate}%

`;
  }

  if (cardData.customerFlow) {
    prompt += `## 客流量分析
- 月度客流量: ${JSON.stringify(cardData.customerFlow.monthly)}
- 平均客流量: ${cardData.customerFlow.average}
- 客流量趋势: ${cardData.customerFlow.trend}

`;
  }

  if (cardData.defeatRate) {
    prompt += `## 战败率分析
- 战败率: ${cardData.defeatRate.rate}%
- 主要战败原因: ${JSON.stringify(cardData.defeatRate.reasons)}

`;
  }

  if (cardData.policy) {
    prompt += `## 政策影响分析
- 月度政策数量: ${JSON.stringify(cardData.policy.monthlyCount || [])}
- 总政策数: ${cardData.policy.totalCount || 0}
- 平均政策数: ${cardData.policy.avgCount || 0}
- 政策影响: ${cardData.policy.impact || '中性'}

`;
  }

  if (cardData.snapshot) {
    prompt += `## 月度快照数据
快照数量: ${cardData.snapshot.count || 0}
`;
    if (cardData.snapshot.data && cardData.snapshot.data.length > 0) {
      prompt += `详细数据:\n`;
      cardData.snapshot.data.forEach(snap => {
        prompt += `- ${snap.month}: 销量${snap.sales}, 客流${snap.traffic}, 线索${snap.leads}, 潜客${snap.potential}, 成交率${snap.rate}\n`;
      });
    }
    prompt += '\n';
  }

  if (cardData.metrics) {
    prompt += `## 核心指标汇总
- 总销量: ${cardData.metrics.totalSales}
- 总客流: ${cardData.metrics.totalTraffic}
- 总线索: ${cardData.metrics.totalLeads}
- 总潜客: ${cardData.metrics.totalPotential}
- 平均转化率: ${cardData.metrics.avgConversionRate}%

`;
  }

  if (cardData.rate) {
    prompt += `## 成交率与战败率分析
- 月度成交率: ${JSON.stringify(cardData.rate.successRate)}
- 月度战败率: ${JSON.stringify(cardData.rate.defeatRate)}
- 平均成交率: ${(cardData.rate.avgSuccessRate * 100).toFixed(1)}%
- 平均战败率: ${(cardData.rate.avgDefeatRate * 100).toFixed(1)}%

`;
  }

  if (cardData.gsev) {
    prompt += `## GSEV指标分析
- 月度GSEV值: ${JSON.stringify(cardData.gsev.gsevValues)}
- 平均GSEV: ${cardData.gsev.avgGsev}
- 趋势: ${cardData.gsev.trend}

`;
  }

  if (cardData.review) {
    prompt += `## 客户评价分析
- 月度评价总数: ${JSON.stringify(cardData.review.totalReviews)}
- 月度好评数: ${JSON.stringify(cardData.review.goodReviews)}
- 月度差评数: ${JSON.stringify(cardData.review.badReviews)}
- 总评价数: ${cardData.review.totalCount}
- 好评率: ${cardData.review.goodRate}%
- 差评率: ${cardData.review.badRate}%

`;
  }

  if (cardData.snapshot) {
    prompt += `## 月度快照数据
- 月份: ${JSON.stringify(cardData.snapshot.months)}
- 销量: ${JSON.stringify(cardData.snapshot.sales)}
- 客流: ${JSON.stringify(cardData.snapshot.traffic)}
- 线索: ${JSON.stringify(cardData.snapshot.leads)}
- 潜客: ${JSON.stringify(cardData.snapshot.potential)}
- 成交率: ${JSON.stringify(cardData.snapshot.rate)}

`;
  }

  if (cardData.metrics) {
    prompt += `## 核心指标汇总
- 总销量: ${cardData.metrics.totalSales}
- 总客流: ${cardData.metrics.totalTraffic}
- 总线索: ${cardData.metrics.totalLeads}
- 总潜客: ${cardData.metrics.totalPotential}
- 平均转化率: ${cardData.metrics.avgConversionRate}%

`;
  }

  if (cardData.rate) {
    prompt += `## 成交率与战败率分析
- 月度成交率: ${JSON.stringify(cardData.rate.successRate)}
- 月度战败率: ${JSON.stringify(cardData.rate.defeatRate)}
- 平均成交率: ${(cardData.rate.avgSuccessRate * 100).toFixed(1)}%
- 平均战败率: ${(cardData.rate.avgDefeatRate * 100).toFixed(1)}%

`;
  }

  if (cardData.gsev) {
    prompt += `## GSEV指标分析
- 月度GSEV值: ${JSON.stringify(cardData.gsev.gsevValues)}
- 平均GSEV: ${cardData.gsev.avgGsev}
- 趋势: ${cardData.gsev.trend}

`;
  }

  if (cardData.review) {
    prompt += `## 客户评价分析
- 月度评价总数: ${JSON.stringify(cardData.review.totalReviews)}
- 月度好评数: ${JSON.stringify(cardData.review.goodReviews)}
- 月度差评数: ${JSON.stringify(cardData.review.badReviews)}
- 总评价数: ${cardData.review.totalCount}
- 好评率: ${cardData.review.goodRate}%
- 差评率: ${cardData.review.badRate}%

`;
  }

  if (cardData.fiveForces) {
    prompt += `## 五力模型评分
- 传播获客力: ${cardData.fiveForces.propagation}/20
- 体验力: ${cardData.fiveForces.experience}/20
- 转化力: ${cardData.fiveForces.conversion}/40
- 服务力: ${cardData.fiveForces.service}/10
- 经营力: ${cardData.fiveForces.operation}/10
- 综合得分: ${cardData.fiveForces.total}/100

`;
  }

  prompt += `
请生成一份结构清晰、数据详实、建议可行的分析报告。报告应使用 Markdown 格式，包含标题、列表、表格等元素。`;

  return prompt;
}

/**
 * 流式调用 DeepSeek API（用于实时显示生成过程）
 * @param {string} prompt - 提示词
 * @param {function} onChunk - 接收到数据块时的回调函数
 * @param {object} options - 可选配置
 */
export async function callDeepSeekStream(prompt, onChunk, options = {}) {
  const {
    model = 'deepseek-chat',
    temperature = 0.7,
    maxTokens = 4000
  } = options;

  try {

    
    // 检查必要的配置
    if (!DEEPSEEK_API_KEY || DEEPSEEK_API_KEY === 'your_api_key_here' || DEEPSEEK_API_KEY === 'sk-your-api-key-here') {
      throw new Error('DeepSeek API Key 未配置，请在项目根目录的 .env 文件中配置 VITE_DEEPSEEK_API_KEY');
    }
    
    if (!DEEPSEEK_API_URL) {
      throw new Error('DeepSeek API URL 未配置，请在项目根目录的 .env 文件中配置 VITE_DEEPSEEK_API_URL');
    }
    
    const response = await fetch(DEEPSEEK_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
      },
      body: JSON.stringify({
        model: model,
        messages: [
          {
            role: 'system',
            content: '你是一位专业的汽车销售数据分析师，擅长分析经销商的销售数据、五力模型、市场趋势等，并提供专业的改进建议。'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: temperature,
        max_tokens: maxTokens,
        stream: true
      })
    });



    if (!response.ok) {
      const errorText = await response.text();
      console.error('API 错误响应:', errorText);
      throw new Error(`DeepSeek API 错误: ${response.statusText} - ${errorText}`);
    }

    console.log('开始读取流数据...');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let chunkCount = 0;

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {

        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            console.log('收到 [DONE] 标记');
            continue;
          }

          try {
            const json = JSON.parse(data);
            const content = json.choices[0]?.delta?.content;
            if (content) {
              chunkCount++;
              onChunk(content);
            }
          } catch (e) {
            console.error('解析流数据失败:', e, '原始数据:', data);
          }
        }
      }
    }
  } catch (error) {
    console.error('DeepSeek 流式调用失败:', error);
    throw error;
  }
}

/**
 * 生成流式销售报告
 * @param {object} cardData - 选中的卡片数据
 * @param {function} onChunk - 接收到数据块时的回调函数
 */
export async function generateSalesReportStream(cardData, onChunk) {
  console.log('generateSalesReportStream 被调用');
  console.log('cardData:', cardData);
  console.log('API Key 存在:', !!DEEPSEEK_API_KEY);
  console.log('API Key 前缀:', DEEPSEEK_API_KEY ? DEEPSEEK_API_KEY.substring(0, 10) : 'undefined');
  
  const prompt = buildSalesReportPrompt(cardData);
  console.log('生成的 prompt 长度:', prompt.length);
  console.log('prompt 预览:', prompt.substring(0, 200));
  
  return await callDeepSeekStream(prompt, onChunk, {
    temperature: 0.7,
    maxTokens: 4000
  });
}
