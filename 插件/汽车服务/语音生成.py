# pip install edge-tts pydub
import asyncio
import edge_tts
from pydub import AudioSegment
import os

VOICE_CONFIG = {
    "sales": "zh-CN-YunxiNeural",  # 专业男声
    "customer": "zh-CN-XiaoxiaoNeural",  # 温柔女声
    "service": "zh-CN-XiaoyiNeural"  # 亲和女声
}

DIALOGUE_SCRIPT = [
    {"role": "sales", "text": "您好，欢迎致电五菱汽车之家！我是顾问小李，请问您想了解一下哪款车型呢？"},
    {"role": "customer", "text": "你好，我最近在看新能源 SUV，预算 20 万左右，有什么推荐吗？"},
    {"role": "sales",
     "text": "有的！我们刚上市的星驰 EV，续航 600 公里，智能驾驶加全景天窗，现在订车立减 8000，还送终身免费保养！"},
    {"role": "customer", "text": "听起来不错！那能安排周末试驾吗？"},
    {"role": "service", "text": "您好，我是售后客服小王，已为您登记周六上午 10 点的试驾预约，稍后短信发送定位，请注意查收。"}
]


async def generate_audio():
    print("🚀 开始生成（Edge-TTS 免费方案）...\n")
    temp_files = []

    for i, item in enumerate(DIALOGUE_SCRIPT):
        role = item["role"]
        text = item["text"]
        voice = VOICE_CONFIG[role]
        temp_file = f"temp_{role}_{i}.mp3"

        print(f"🎙️ 生成 {voice}: {text[:20]}...")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(temp_file)

        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 1000:
            print(f"✅ {temp_file} 生成成功")
            temp_files.append(temp_file)
        else:
            print(f"❌ {temp_file} 生成失败")

        await asyncio.sleep(0.3)

    # 合并音频
    if temp_files:
        combined = AudioSegment.empty()
        for i, f in enumerate(temp_files):
            combined += AudioSegment.from_mp3(f)
            if i < len(temp_files) - 1:
                combined += AudioSegment.silent(duration=400)

        combined.export("auto_sales_dialogue.mp3", format="mp3", bitrate="128k")
        print(f"\n🎧 合并完成：auto_sales_dialogue.mp3 | 时长：{len(combined) / 1000:.1f}秒")

        # 清理
        for f in temp_files:
            os.remove(f)

    return "_sales_dialogue.mp3"


if __name__ == "__main__":
    asyncio.run(generate_audio())