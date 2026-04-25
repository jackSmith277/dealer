import numpy as np
import jieba
import os
import io
import base64
import warnings
from collections import Counter

warnings.filterwarnings('ignore')

try:
    from PIL import Image
except ImportError:
    print("请先安装Pillow库: pip install pillow")

try:
    from wordcloud import WordCloud, STOPWORDS
except ImportError:
    print("请先安装wordcloud库: pip install wordcloud")


class WordCloudGenerator:
    def __init__(self, theme='vibrant'):
        self.theme = theme
        self.color_maps = {
            'corporate': ['#2C3E50', '#3498DB', '#2980B9', '#1ABC9C', '#16A085'],
            'vibrant': ['#E67E22', '#E74C3C', '#F1C40F', '#2ECC71', '#9B59B6'],
            'dark': ['#34495E', '#7F8C8D', '#95A5A6', '#BDC3C7', '#ECF0F1'],
            'elegant': ['#8E44AD', '#3498DB', '#E84393', '#F39C12', '#1ABC9C']
        }
        self.stopwords = set(STOPWORDS) if 'STOPWORDS' in dir() else set()
        self.custom_stopwords = {
            '可以', '进行', '具有', '对于', '通过', '使用', '能够',
            '需要', '以及', '其中', '等', '了', '的', '在', '和',
            '与', '或', '一个', '这个', '那个', '这些', '那些',
            '我们', '他们', '它们', '它', '她', '他', '是', '有',
            '都', '也', '就', '不', '人', '很', '到', '说', '要',
            '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
            '那', '但', '又', '而', '且', '或', '如果', '因为', '所以',
            '虽然', '但是', '然后', '还是', '只是', '就是', '不是',
            '什么', '怎么', '为什么', '哪', '哪里', '怎样', '多少',
            '已经', '还有', '一样', '一下', '一点', '一些', '这种',
            '那种', '某个', '某些', '每个', '所有', '任何', '其他',
            '其实', '确实', '真的', '真是', '实在', '确实', '比较',
            '相当', '非常', '特别', '十分', '极其', '尤其', '更加',
            '最', '更', '太', '挺', '够', '稍', '略', '较', '最为',
            '一下', '一点', '一些', '几个', '多少', '许多', '很多',
            '这么', '那么', '多么', '如何', '怎样', '为何', '几',
            '做', '作', '给', '让', '把', '被', '比', '跟', '像',
            '对', '向', '从', '往', '到', '于', '为', '以', '及',
            '并', '且', '而', '或', '但', '却', '才', '只', '仅',
            '还', '再', '也', '都', '既', '即', '便', '竟', '竟',
            '居然', '竟然', '果然', '仍然', '依然', '当然', '固然',
            '一定', '必须', '应该', '可能', '大概', '也许', '大约',
            '差不多', '几乎', '简直', '完全', '非常', '特别', '尤其',
            '甚至', '连', '带', '加', '减', '乘', '除', '等于',
            '起来', '下来', '出来', '进来', '回来', '过来', '进去',
            '上去', '下去', '出去', '进去', '回来', '过来', '开来',
            '觉得', '认为', '以为', '感觉', '感到', '发现', '知道',
            '了解', '认识', '理解', '明白', '清楚', '看到', '听到',
            '觉得', '想', '要', '能', '会', '可以', '应该', '必须',
            '可能', '得', '地', '得', '着', '过', '来', '去',
            '这里', '那里', '哪里', '这边', '那边', '哪边',
            '今天', '明天', '昨天', '前天', '后天', '现在', '以后',
            '以前', '之前', '之后', '当时', '此时', '那时',
            '一种', '一样', '一般', '一定', '一起', '一直', '一样',
            '第一', '第二', '第三', '最后', '首先', '其次', '然后',
            '终于', '结果', '原来', '本来', '其实', '实际上',
            '车', '辆', '次', '个', '只', '些', '点', '下', '上',
            '里', '外', '内', '中', '前', '后', '左', '右', '上', '下',
            '多', '少', '大', '小', '长', '短', '高', '低', '快', '慢',
            '新', '旧', '好', '坏', '对', '错', '真', '假', '是', '非',
            '买', '卖', '开', '关', '来', '去', '进', '出', '上', '下',
            '提', '试', '看', '想', '说', '问', '答', '讲', '谈', '聊'
        }
        self.stopwords.update(self.custom_stopwords)
        self.font_path = self._get_chinese_font()
        
        self.useful_word_patterns = [
            '动力', '操控', '舒适', '外观', '内饰', '配置', '空间',
            '油耗', '价格', '服务', '质量', '性能', '安全', '品牌',
            '加速', '刹车', '转向', '悬挂', '底盘', '发动机', '变速箱',
            '座椅', '空调', '音响', '导航', '屏幕', '天窗', '轮毂',
            '颜色', '造型', '设计', '做工', '用料', '材质', '手感',
            '噪音', '隔音', '减震', '稳定', '灵活', '精准', '平顺',
            '满意', '喜欢', '推荐', '值得', '不错', '很好', '舒服',
            '问题', '缺点', '不足', '遗憾', '失望', '不满', '投诉',
            '优惠', '划算', '性价比', '保值', '落地', '预算', '首付'
        ]

    def _get_chinese_font(self):
        project_fonts = [
            os.path.join(os.path.dirname(__file__), 'fonts', 'simhei.ttf'),
            os.path.join(os.path.dirname(__file__), 'fonts', 'msyh.ttc'),
            os.path.join(os.path.dirname(__file__), 'fonts', 'simsun.ttc'),
        ]
        for font in project_fonts:
            if os.path.exists(font):
                return font
        system_fonts = [
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simkai.ttf',
            '/System/Library/Fonts/PingFang.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc',
            '/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
        for font in system_fonts:
            if os.path.exists(font):
                return font
        return None

    def _is_meaningful_word(self, word):
        if len(word) < 2:
            return False
        if word.isdigit():
            return False
        if word in self.stopwords:
            return False
        if all(c.isdigit() or c in '年月日时分秒' for c in word):
            return False
        if word.startswith('很') or word.startswith('太') or word.startswith('挺'):
            if len(word) == 2:
                return False
        if word.endswith('的') or word.endswith('地') or word.endswith('得'):
            return False
        if word in ['一点', '一些', '几个', '多少', '很多', '这么', '那么']:
            return False
        return True

    def segment_chinese(self, text):
        try:
            words = jieba.lcut(text)
        except:
            words = text.split()
        
        filtered = []
        for word in words:
            word = word.strip()
            if self._is_meaningful_word(word):
                filtered.append(word)
        return ' '.join(filtered)

    def get_word_frequencies(self, text, is_chinese=True):
        if is_chinese:
            processed_text = self.segment_chinese(text)
        else:
            processed_text = text.lower()
        
        words = processed_text.split()
        if not words:
            return {}
        
        word_freq = Counter(words)
        
        filtered_freq = {}
        for word, freq in word_freq.items():
            if freq < 1:
                continue
            if len(word) < 2:
                continue
            if word in self.stopwords:
                continue
            if all(c.isdigit() or c in '年月日时分秒%-./' for c in word):
                continue
            if word in ['一点', '一些', '几个', '多少', '很多', '这么', '那么', '这样', '那样']:
                continue
            if word.startswith('很') or word.startswith('太') or word.startswith('挺'):
                if len(word) == 2:
                    continue
            if word.endswith('的') or word.endswith('地') or word.endswith('得'):
                continue
            filtered_freq[word] = freq
        
        if filtered_freq:
            max_freq = max(filtered_freq.values())
            min_threshold = max(1, max_freq // 30)
            filtered_freq = {word: freq for word, freq in filtered_freq.items() if freq >= min_threshold}
        
        return filtered_freq

    def generate_color_func(self, word=None, font_size=None, position=None,
                            orientation=None, font_path=None, random_state=None):
        import random
        colors = self.color_maps.get(self.theme, self.color_maps['vibrant'])
        intensity = min(0.6 + (font_size / 100) * 0.4, 1.0) if font_size else 0.8
        
        if word:
            base_color = colors[hash(word) % len(colors)]
        else:
            base_color = random.choice(colors)
        
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        
        r = min(255, int(r * (0.7 + intensity * 0.3)))
        g = min(255, int(g * (0.7 + intensity * 0.3)))
        b = min(255, int(b * (0.7 + intensity * 0.3)))
        
        return f"rgb({r}, {g}, {b})"

    def generate_wordcloud_base64(self, word_freq, width=800, height=500, 
                                   background_color='white', max_words=100, 
                                   max_font_size=80):
        if not word_freq:
            return None
        
        wordcloud_params = {
            'width': width,
            'height': height,
            'background_color': background_color,
            'max_words': max_words,
            'max_font_size': max_font_size,
            'min_font_size': 7,
            'relative_scaling': 0.25,
            'color_func': self.generate_color_func,
            'font_path': self.font_path,
            'random_state': 42,
            'collocations': False,
            'prefer_horizontal': 0.75,
            'margin': 0
        }
        
        wc = WordCloud(**wordcloud_params)
        wc.generate_from_frequencies(word_freq)
        
        img_buffer = io.BytesIO()
        wc.to_image().save(img_buffer, format='PNG', optimize=True)
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"

    def generate_wordcloud_for_sentiment(self, comments, sentiment_type='all', 
                                          width=900, height=550):
        text = ' '.join([c.get('content', '') for c in comments])
        
        if not text.strip():
            return None
        
        word_freq = self.get_word_frequencies(text, is_chinese=True)
        
        if not word_freq:
            return None
        
        scored_words = {}
        for word, freq in word_freq.items():
            score = freq
            if word in self.useful_word_patterns:
                score *= 1.5
            if len(word) >= 3:
                score *= 1.2
            scored_words[word] = int(score)
        
        sorted_words = sorted(scored_words.items(), key=lambda x: x[1], reverse=True)
        top_words = dict(sorted_words[:350])
        
        theme_map = {
            'positive': 'vibrant',
            'negative': 'dark',
            'neutral': 'corporate',
            'all': 'vibrant'
        }
        
        self.theme = theme_map.get(sentiment_type, 'vibrant')
        
        return self.generate_wordcloud_base64(
            top_words, 
            width=width, 
            height=height,
            max_words=350,
            max_font_size=55
        )

    def generate_circular_wordcloud(self, positive_words, negative_words, neutral_words,
                                     width=900, height=600):
        all_word_freq = {}
        
        def filter_and_add_words(word_list, weight=1.0):
            for word_data in word_list:
                name = word_data.get('name', '')
                value = word_data.get('value', 1)
                if not name:
                    continue
                if len(name) < 2:
                    continue
                if name in self.stopwords:
                    continue
                if name in ['一点', '一些', '几个', '多少', '很多', '这么', '那么', '这样', '那样']:
                    continue
                if name.startswith('很') or name.startswith('太') or name.startswith('挺'):
                    if len(name) == 2:
                        continue
                if name.endswith('的') or name.endswith('地') or name.endswith('得'):
                    continue
                score = value * weight
                if name in self.useful_word_patterns:
                    score *= 1.5
                if len(name) >= 3:
                    score *= 1.2
                all_word_freq[name] = all_word_freq.get(name, 0) + int(score)
        
        filter_and_add_words(positive_words[:200], 1.0)
        filter_and_add_words(neutral_words[:150], 0.8)
        filter_and_add_words(negative_words[:120], 1.0)
        
        if not all_word_freq:
            return None
        
        sorted_words = sorted(all_word_freq.items(), key=lambda x: x[1], reverse=True)
        top_words = dict(sorted_words[:300])
        
        self.theme = 'vibrant'
        
        return self.generate_wordcloud_base64(
            top_words,
            width=width,
            height=height,
            max_words=280,
            max_font_size=55
        )


wordcloud_generator = WordCloudGenerator(theme='vibrant')
