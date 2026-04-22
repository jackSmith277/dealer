import time
import requests
import json
import os
from datetime import datetime
from pathlib import Path
from dashscope.multimodal.tingwu.tingwu import TingWu
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

load_dotenv()

# ============== 配置区域 ==============
API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-764a502f6eef4b7999800d65212d282f").strip()
BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = 'tingwu-automotive-service-insights'
APP_ID = "tw_bEFSoD4kIq1w"
MAX_POLL_ATTEMPTS = 30
POLL_INTERVAL = 5
OUTPUT_DIR = "reports"
# Flask 服务配置
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000


# ==============

# ============== 新增：音频文件处理工具函数 ==============
def is_audio_file(file_path):
    """判断是否为支持的音频文件"""
    if not os.path.isfile(file_path):
        return False
    audio_exts = {'.mp3', '.wav', '.pcm', '.aac', '.amr', '.opus', '.speex', '.flac', '.m4a'}
    return Path(file_path).suffix.lower() in audio_exts


def is_text_input(input_data):
    """判断是否为文本输入（非文件路径的字符串）"""
    if not isinstance(input_data, str):
        return False
    if is_audio_file(input_data):
        return False
    if input_data.startswith(("http://", "https://")):
        return False
    return len(input_data.strip()) > 10


def upload_to_oss(local_file_path, oss_bucket, oss_endpoint, oss_access_key_id,
                  oss_access_key_secret, oss_file_key=None):
    """
    上传本地音频文件到阿里云 OSS（需安装：pip install oss2）
    返回可公开访问的文件 URL（带签名，默认有效期 7 天）
    """
    try:
        import oss2
        auth = oss2.Auth(oss_access_key_id, oss_access_key_secret)
        bucket = oss2.Bucket(auth, oss_endpoint, oss_bucket)

        if oss_file_key is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(local_file_path)
            oss_file_key = f"tingwu_audio/{timestamp}_{filename}"

        bucket.put_object_from_file(oss_file_key, local_file_path)
        print(f"✅ 文件已上传至 OSS: {oss_file_key}")

        url = bucket.sign_url('GET', oss_file_key, 7 * 24 * 3600)
        return url
    except ImportError:
        print("⚠️ 未安装 oss2 库，请使用：pip install oss2")
        return None
    except Exception as e:
        print(f"❌ OSS 上传失败：{e}")
        return None


def get_audio_url(input_source, input_type):
    """根据输入类型获取音频文件的 OSS URL"""
    if input_type == "text":
        return None

    if input_type == "url":
        return input_source.strip()

    if input_type == "file":
        if not os.path.isfile(input_source):
            print(f"❌ 文件不存在：{input_source}")
            return None

        oss_bucket = os.getenv("OSS_BUCKET")
        oss_endpoint = os.getenv("OSS_ENDPOINT")
        oss_ak = os.getenv("OSS_ACCESS_KEY_ID")
        oss_sk = os.getenv("OSS_ACCESS_KEY_SECRET")

        if not all([oss_bucket, oss_endpoint, oss_ak, oss_sk]):
            print("❌ 未配置 OSS 环境变量，请设置：OSS_BUCKET, OSS_ENDPOINT, OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET")
            return None

        return upload_to_oss(
            local_file_path=input_source,
            oss_bucket=oss_bucket,
            oss_endpoint=oss_endpoint,
            oss_access_key_id=oss_ak,
            oss_access_key_secret=oss_sk
        )

    return None


def detect_input_type(input_source, hint_type="auto"):
    """自动检测输入类型"""
    if hint_type != "auto":
        return hint_type

    if is_audio_file(input_source):
        return "file"
    elif isinstance(input_source, str) and input_source.startswith(("http://", "https://")):
        return "url"
    else:
        return "text"


# ============== 新增：Flask API 服务 ==============
app = Flask(__name__)
CORS(app)


@app.route('/api/insight-analyze', methods=['POST'])
def api_insight_analyze():
    """服务洞察分析 API 接口"""
    try:
        input_type = request.form.get('input_type', 'text')

        if input_type == 'text':
            text_content = request.form.get('text_content', '')
            if not text_content.strip():
                return jsonify({'ok': False, 'error': '文本内容不能为空'}), 400

            result = analyze_insight_internal(text_content, 'text')

        elif input_type == 'file':
            if 'audio_file' not in request.files:
                return jsonify({'ok': False, 'error': '未找到音频文件'}), 400

            audio_file = request.files['audio_file']

            # 保存临时文件
            temp_dir = "temp_audio"
            os.makedirs(temp_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file_path = os.path.join(temp_dir, f"{timestamp}_{audio_file.filename}")
            audio_file.save(temp_file_path)

            try:
                result = analyze_insight_internal(temp_file_path, 'file')
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            return jsonify({'ok': False, 'error': '不支持的输入类型'}), 400

        if result:
            # 读取生成的 Markdown 报告
            report_content = ""
            if os.path.exists(result['report_md']):
                with open(result['report_md'], 'r', encoding='utf-8') as f:
                    report_content = f.read()

            return jsonify({
                'ok': True,
                'success': True,
                'dataId': result.get('dataId'),
                'summary': {
                    'total_items': len(result.get('matched', [])) + len(result.get('unmatched', [])),
                    'matched': len(result.get('matched', [])),
                    'unmatched': len(result.get('unmatched', [])),
                    'hit_rate': f"{len(result.get('matched', [])) / (len(result.get('matched', [])) + len(result.get('unmatched', []))) * 100:.1f}%" if (
                                                                                                                                                                    len(result.get(
                                                                                                                                                                        'matched',
                                                                                                                                                                        [])) + len(
                                                                                                                                                                result.get(
                                                                                                                                                                    'unmatched',
                                                                                                                                                                    []))) > 0 else "0%"
                },
                'markdown_report': report_content,
                'report_file': result.get('report_md'),
                'data_json': result.get('data_json')
            })
        else:
            return jsonify({'ok': False, 'error': '分析失败'}), 500

    except Exception as e:
        print(f"❌ API 分析错误：{e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/insight-report/<report_id>', methods=['GET'])
def api_get_report(report_id):
    """获取指定报告"""
    try:
        report_path = os.path.join(OUTPUT_DIR, f"auto_service_report_{report_id}.md")
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'ok': True, 'content': content})
        else:
            return jsonify({'ok': False, 'error': '报告不存在'}), 404
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


def analyze_insight_internal(input_source, input_type="auto"):
    """内部分析函数（与 main 函数逻辑相同）"""
    print("🚀 开始汽车服务质检分析...")

    detected_type = detect_input_type(input_source, input_type)
    print(f"📥 输入类型：{detected_type}")

    if detected_type == "text":
        print("📝 使用文本输入模式")
        task_input = {
            "appId": APP_ID,
            "text": input_source,
            "task": "createTask"
        }
        input_info = {"type": "text", "source": input_source[:100] + "..." if len(input_source) > 100 else input_source}
    else:
        print(f"🎵 使用音频输入模式 ({detected_type})")
        audio_url = get_audio_url(input_source, detected_type)
        if not audio_url:
            print("❌ 无法获取音频文件 URL，请检查配置或输入")
            return None

        task_input = {
            "appId": APP_ID,
            "fileUrl": audio_url,
            "task": "createTask"
        }
        input_info = {"type": detected_type, "source": input_source}

    create_resp = TingWu.call(
        model=MODEL,
        user_defined_input=task_input,
        api_key=API_KEY,
        base_address=BASE_URL,
    )

    if create_resp.get("status_code") != 200:
        print(f"❌ 创建失败：{create_resp}")
        return None

    data_id = create_resp.get("output", {}).get("dataId")
    if not data_id:
        print(f"❌ 无 dataId: {create_resp}")
        return None

    print(f"✅ 任务创建：{data_id}")

    output = poll_task_result(API_KEY, BASE_URL, data_id, MODEL)
    if not output:
        return None

    results = {}
    for key, name in [
        ("transcriptionPath", "转写"),
        ("serviceInsightsPath", "质检"),
        ("saleInsightsPath", "销售")
    ]:
        url = output.get(key)
        if url:
            print(f"  📥 {name}...")
            results[key] = download_json_from_oss(url)

    trans = results.get("transcriptionPath")
    matched, unmatched = parse_insights(results.get("serviceInsightsPath"))
    sale = results.get("saleInsightsPath")

    print_console_summary(matched, unmatched, sale)

    print("\n📝 生成 Markdown 报告...")
    md_content = generate_markdown_report(trans, matched, unmatched, sale, data_id, input_info)
    md_file = save_markdown_report(md_content)

    json_file = os.path.join(OUTPUT_DIR, f"data_{os.path.basename(md_file).replace('.md', '.json')}")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "transcription": trans,
            "matched": matched,
            "unmatched": unmatched,
            "sale": sale,
            "input_info": input_info
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 原始数据已保存：{json_file}")

    return {
        "dataId": data_id,
        "input_type": detected_type,
        "input_source": input_source,
        "matched": matched,
        "unmatched": unmatched,
        "report_md": md_file,
        "data_json": json_file
    }


def start_flask_server():
    """启动 Flask 服务"""
    print(f"🚀 启动 Flask 服务：http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)


# ============== 原有函数保持不变 ==============
def download_json_from_oss(oss_url):
    """下载并解析 OSS 上的 JSON 结果"""
    try:
        response = requests.get(oss_url.strip(), timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 下载失败：{e}")
        return None


def poll_task_result(api_key, base_url, data_id, model):
    """轮询等待任务完成"""
    for attempt in range(MAX_POLL_ATTEMPTS):
        print(f"🔄 轮询 {attempt + 1}/{MAX_POLL_ATTEMPTS}...")
        resp = TingWu.call(
            model=model,
            user_defined_input={"task": "getTask", "dataId": data_id},
            api_key=api_key,
            base_address=base_url,
        )

        output = resp.get("output", {})
        status = output.get("status")

        if status == 0:
            print("✅ 任务完成！")
            return output
        elif status == 2:
            print(f"❌ 任务失败：{output.get('errorCode')}")
            return None
        time.sleep(POLL_INTERVAL)

    print("⏰ 轮询超时")
    return None


def parse_insights(insights_data):
    """解析质检项，分离命中/未命中"""
    if not insights_data:
        return [], []
    items = insights_data if isinstance(insights_data, list) else insights_data.get("serviceInsights", [])
    matched = [i for i in items if isinstance(i, dict) and i.get("matched") is True]
    unmatched = [i for i in items if isinstance(i, dict) and i.get("matched") is not True]
    return matched, unmatched


def format_transcription_md(trans_data, max_show=3):
    """格式化转写文本为 Markdown"""
    if not trans_data:
        return "> ⚠️ 无转写内容"
    paragraphs = trans_data if isinstance(trans_data, list) else trans_data.get("paragraphs", [])
    if not paragraphs:
        return "> ⚠️ 无转写内容"

    lines = []
    for p in paragraphs[:max_show]:
        if not isinstance(p, dict):
            continue
        speaker = p.get("speakerId", "?")
        words = p.get("words", [])
        text = " ".join([w.get("text", " ") if isinstance(w, dict) else str(w) for w in words])
        lines.append(f"**说话人{speaker}**: {text}")

    if len(paragraphs) > max_show:
        lines.append(f"\n> *... 还有 {len(paragraphs) - max_show} 段*")

    return "\n\n".join(lines)


def format_insights_table_md(matched, unmatched, show_unmatched_limit=10):
    """格式化质检项为 Markdown 表格"""
    lines = []
    lines.append("### ✅ 命中项（符合规范）")
    if matched:
        lines.append("| 序号 | 质检项 | 说明 | 得分 |")
        lines.append("|------|--------|------|------|")
        for i, item in enumerate(matched, 1):
            title = item.get("title", "未知项")
            remarks = item.get("remarks", " ").replace("|", "\\|")[:80]
            score = item.get("score", "-")
            lines.append(f"| {i} | {title} | {remarks}... | {score} |")
    else:
        lines.append("> ⚠️ 本次对话无命中质检项")

    lines.append("")

    lines.append("### ❌ 未命中项（待改进）")
    if unmatched:
        lines.append(f"> 共 {len(unmatched)} 项未命中，以下是前 {min(show_unmatched_limit, len(unmatched))} 项：")
        lines.append("")
        lines.append("| 序号 | 质检项 | 说明 |")
        lines.append("|------|--------|------|")
        for i, item in enumerate(unmatched[:show_unmatched_limit], 1):
            title = item.get("title", "未知项")
            remarks = item.get("remarks", " ").replace("|", "\\|")[:60]
            lines.append(f"| {i} | {title} | {remarks}... |")
        if len(unmatched) > show_unmatched_limit:
            lines.append(f"\n> *... 还有 {len(unmatched) - show_unmatched_limit} 项*")
    else:
        lines.append("> 🎉 全部质检项均命中！")

    return "\n".join(lines)


def format_sale_summary_md(sale_data):
    """格式化销售分析为 Markdown"""
    if not sale_data:
        return "> ⚠️ 无销售分析数据"
    if isinstance(sale_data, dict):
        matched = sale_data.get("matchedSum", 0)
        missed = sale_data.get("missedSum", 0)
        total = matched + missed
        rate = f"{matched / total * 100:.1f}%" if total > 0 else "N/A"

        bar_len = 20
        filled = int(matched / total * bar_len) if total > 0 else 0
        progress = "█" * filled + "░" * (bar_len - filled)

        return f"""| 指标 | 数值 |
| ---|---|
| ✅ 命中项 | {matched} |
| ❌ 未命中项 | {missed} |
| 📊 总计 | {total} |
| 📈 完成率 | {rate} |
进度可视化：`{progress}` {rate}"""
    elif isinstance(sale_data, list):
        return f"> 📋 销售分析记录：{len(sale_data)} 条"
    return "> ⚠️ 数据格式异常"


def generate_markdown_report(trans_data, matched, unmatched, sale_data, data_id, input_info=None):
    """生成完整 Markdown 报告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_items = len(matched) + len(unmatched)
    hit_rate = f"{len(matched) / total_items * 100:.1f}%" if total_items > 0 else "0%"

    input_line = ""
    if input_info:
        input_line = f"> **输入类型**: {input_info.get('type')}  \n> **输入源**: `{input_info.get('source', 'N/A')[:100]}`  \n"

    report = f"""# 🚗 汽车服务质检分析报告
任务 ID: `{data_id}`  {input_line}> 生成时间：{timestamp}  \n> 分析模型：{MODEL}

## 📋 报告摘要
| 指标 | 数值 |
| ---|---|
| 🔍 质检项总数 | {total_items} |
| ✅ 命中项 | {len(matched)} |
| ❌ 未命中项 | {len(unmatched)} |
| 📈 命中率 | {hit_rate} |

## 💬 对话转写
{format_transcription_md(trans_data)}

## 🔍 服务质检详情
{format_insights_table_md(matched, unmatched)}

## 📊 销售流程分析
{format_sale_summary_md(sale_data)}

## 📌 说明:
- ✅ 命中：销售人员执行了该规范动作
- ❌ 未命中：销售人员未执行或执行不到位
- 建议针对未命中项进行针对性培训改进

本报告由 阿里云听悟·汽车服务洞察 自动生成"""
    return report


def save_markdown_report(content, filename=None):
    """保存 Markdown 报告到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"auto_service_report_{timestamp}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📄 Markdown 报告已保存：{filepath}")
    return filepath


def print_console_summary(matched, unmatched, sale_data):
    """控制台简洁输出（配合 Markdown 使用）"""
    total = len(matched) + len(unmatched)
    rate = len(matched) / total * 100 if total > 0 else 0
    print(f"\n📊 质检速览：✅{len(matched)} / ❌{len(unmatched)} / 命中率 {rate:.1f}%")

    if matched:
        print(f"\n🎯 命中项 ({len(matched)}):")
        for item in matched:
            print(f"  • ✅ {item.get('title')}: {item.get('remarks', '')[:50]}...")

    if unmatched:
        print(f"\n⚠️  未命中项 ({len(unmatched)}), 前 3 项:")
        for item in unmatched[:3]:
            print(f"  • ❌ {item.get('title')}: {item.get('remarks', '')[:50]}...")


def main(input_source, input_type="auto"):
    """主函数 - 支持文本、本地音频文件、OSS 音频 URL 三种输入方式"""
    return analyze_insight_internal(input_source, input_type)


if __name__ == '__main__':
    # 启动 Flask API 服务
    print("=" * 50)
    print("🚗 汽车服务质检分析系统 - Flask API 服务")
    print("=" * 50)

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 启动 Flask 服务（在新线程中）
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()

    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")