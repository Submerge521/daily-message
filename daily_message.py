import requests
import os
import json
from datetime import datetime, date
import random
import time


# --- 从环境变量获取配置 ---
APPID = os.getenv('WECHAT_APPID')
APPSECRET = os.getenv('WECHAT_APPSECRET')
TEMPLATE_ID = os.getenv('WECHAT_TEMPLATE_ID')
USER_ID = os.getenv('WECHAT_USER_ID')
CITY = os.getenv('CITY', '广州')
BIRTHDAY = os.getenv('BIRTHDAY', '02-27')  # 格式: MM-DD
RELATIONSHIP_DATE = os.getenv('RELATIONSHIP_DATE', '2025-08-18')  # 格式: YYYY-MM-DD
GF_NAME = os.getenv('GF_NAME', '小睿')
CONSTELLATION = os.getenv('CONSTELLATION', '白羊座')  # 星座名称

# --- 新增：高德地图 API Key ---
AMAP_KEY = os.getenv('AMAP_KEY')  # 请务必设置此环境变量

# --- 新增：聚合数据星座 API Key ---
# JUHE_CONSTELLATION_KEY = os.getenv('JUHE_CONSTELLATION_KEY')  # 请务必设置此环境变量


class WeChatMessage:
    def __init__(self):
        self.access_token = None
        self.token_expire_time = 0
        self.generated_data = {}  # 用于存储生成的数据，便于调试和返回
        # 初始化恋爱日期
        self.init_relationship_date()

    def init_relationship_date(self):
        """初始化恋爱日期"""
        try:
            self.relationship_start = datetime.strptime(RELATIONSHIP_DATE, '%Y-%m-%d').date()
        except Exception as e:
            print(f"恋爱日期格式错误，使用默认值: {e}")
            self.relationship_start = date(2023, 1, 1)

    def get_access_token(self):
        """获取微信access_token，带重试机制"""
        if not APPID or not APPSECRET:
            print("❌ 未配置 WECHAT_APPID 或 WECHAT_APPSECRET")
            return None
        if self.access_token and datetime.now().timestamp() < self.token_expire_time:
            return self.access_token
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
        max_retries = 3
        retry_delay = 2  # 秒
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    # 提前300秒过期，避免刚好在发送时过期
                    self.token_expire_time = datetime.now().timestamp() + data['expires_in'] - 300
                    print("✅ 获取access_token成功")
                    return self.access_token
                else:
                    print(f"❌ 获取access_token失败: {data}")
            except Exception as e:
                print(f"❌ 获取access_token异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        return None

    def get_weather(self):
        """获取天气信息 - 使用高德天气 API，并返回精简版"""
        print("正在获取天气信息...")
        if not AMAP_KEY:
            print("⚠️ 未配置高德地图 API Key (AMAP_KEY)，使用本地天气数据")
            return self._get_local_weather_summary()
        try:
            # 1. 通过城市名获取 adcode (区域编码)
            geo_url = f"https://restapi.amap.com/v3/geocode/geo?address={CITY}&key={AMAP_KEY}"
            geo_response = requests.get(geo_url, timeout=10)
            geo_data = geo_response.json()
            if geo_data.get('status') == '1' and geo_data.get('geocodes'):
                adcode = geo_data['geocodes'][0]['adcode']
                print(f"✅ 城市 {CITY} 对应的 adcode: {adcode}")
            else:
                print(f"❌ 获取城市 {CITY} 的 adcode 失败: {geo_data}")
                return self._get_local_weather_summary()

            # 2. 通过 adcode 获取天气信息
            weather_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={AMAP_KEY}&extensions=base"
            weather_response = requests.get(weather_url, timeout=10)
            weather_data = weather_response.json()
            if weather_data.get('status') == '1' and weather_data.get('lives'):
                live_weather = weather_data['lives'][0]
                weather = live_weather['weather']
                temperature = live_weather['temperature']
                # 精简：只取天气和温度，提示用最相关的
                tip = self._get_weather_tip(weather)
                # 🔑 精简版格式：天气 + 温度 + 最相关提示
                result = f"{weather} {temperature}°C | {tip}"
                print(f"✅ 天气获取成功 (精简): {result}")
                return result
            else:
                print(f"❌ 获取天气信息失败: {weather_data}")
                return self._get_local_weather_summary()
        except Exception as e:
            print(f"❌ 获取天气信息异常: {e}")
            return self._get_local_weather_summary()

    def _get_local_weather_summary(self):
        """获取本地天气数据的精简版"""
        now = datetime.now()
        month = now.month
        day_temp = random.randint(15, 35)
        # 🔑 精简：只保留核心天气和一个提示
        if month in [12, 1, 2]:  # 冬季
            weather = "晴"
            temp = day_temp
            tip = "冬天来了，记得穿暖暖"
        elif month in [3, 4, 5]:  # 春季
            weather = "晴"
            temp = day_temp
            tip = "春暖花开，适合散步"
        elif month in [6, 7, 8]:  # 夏季
            weather = "晴"
            temp = day_temp
            tip = "热浪来袭，注意防暑"
        else:  # 秋季
            weather = "晴"
            temp = day_temp
            tip = "秋高气爽，很舒服呢"

        result = f"{weather} {temp}°C | {tip}"
        print(f"⚠️ 使用本地天气数据 (精简): {result}")
        return result

    def _get_weather_tip(self, weather_type):
        """根据天气类型获取提示"""
        tips = {
            "晴": "阳光很好，记得涂防晒霜哦~",
            "多云": "云朵飘飘，心情也会变好",
            "阴": "阴天也要保持好心情呀",
            "雨": "记得带伞，不想你淋雨",
            "雪": "下雪啦！要穿暖暖的",
            "雾": "雾天注意安全，慢慢走",
            "雷阵雨": "雷雨天，注意安全，避免外出",
            "小雨": "毛毛雨，带把小伞更贴心",
            "中雨": "雨有点大，记得带伞",
            "大雨": "雨很大，注意安全，减少外出",
            "暴雨": "暴雨预警，请注意防范！",
        }
        return tips.get(weather_type, "天气多变，要照顾好自己哦")

    def calculate_days_until_birthday(self):
        """计算距离生日的天数"""
        try:
            today = date.today()
            year = today.year
            month, day = map(int, BIRTHDAY.split('-'))
            # 处理2月29日的特殊情况
            if month == 2 and day == 29 and not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
                birthday_this_year = date(year, 3, 1)
            else:
                birthday_this_year = date(year, month, day)
            if today > birthday_this_year:
                next_year = year + 1
                # 再次处理明年2月29日的情况
                if month == 2 and day == 29 and not (
                        next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0)):
                    birthday_next_year = date(next_year, 3, 1)
                else:
                    birthday_next_year = date(next_year, month, day)
                days_left = (birthday_next_year - today).days
            else:
                days_left = (birthday_this_year - today).days
            # 生成有趣的倒计时描述
            if days_left == 0:
                return "🎉 今天是生日！生日快乐我的宝贝！"
            elif days_left == 1:
                return "🌟 明天生日！已经准备好惊喜啦~"
            elif days_left < 7:
                return f"🎂 还有{days_left}天！超级期待！"
            elif days_left < 30:
                return f"💝 还有{days_left}天，每天都在想你"
            elif days_left < 100:
                return f"📅 还有{days_left}天，期待与你庆祝"
            else:
                return f"🗓️ 还有{days_left}天，但爱你的心从不停止"
        except Exception as e:
            print(f"计算生日失败: {e}")
            return "🎁 生日总是最特别的日子"

    def calculate_love_days(self):
        """计算恋爱天数"""
        try:
            today = date.today()
            days = (today - self.relationship_start).days
            if days <= 0:
                return "💘 今天是我们在一起的第一天！"
            elif days % 365 == 0:
                years = days // 365
                return f"💑 我们已经在一起{years}年啦！{days}天的幸福时光~"
            elif days % 100 == 0:
                return f"💞 第{days}天啦！百天纪念快乐~"
            elif days % 30 == 0:
                return f"💖 已经{days}天了，每月都有新甜蜜~"
            else:
                return f"❤️ 我们已经在一起{days}天啦~"
        except Exception as e:
            print(f"计算恋爱天数失败: {e}")
            return "💓 每一天都值得珍惜"

    def get_horoscope(self):
        """获取星座运势 - 使用 Juhe (聚合数据) 的 API，返回精简版"""
        print("正在获取星座运势...")
        # if not JUHE_CONSTELLATION_KEY:
        #     print("⚠️ 未配置聚合数据星座 API Key (JUHE_CONSTELLATION_KEY)，使用本地模拟数据")
        # return self._get_local_horoscope_summary()

        try:
            url = "http://web.juhe.cn:8080/constellation/getAll"
            params = {
                'consName': CONSTELLATION,
                'type': 'today',
                # 'key': JUHE_CONSTELLATION_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data.get('error_code') == 0 and 'result' in data:
                horoscope_data = data['result']
                # 🔑 精简：提取更具体的字段，而不是冗长的 summary
                # 假设 API 返回中有更具体的字段，比如 'text' 或 'day'
                # 这里我们尝试提取 'text' 字段，它通常更简洁
                # 如果没有 'text'，再用 'summary' 并进行截断
                full_text = horoscope_data.get('text') or horoscope_data.get('summary', '')
                if full_text:
                    # 🔑 进一步精简：取前两句话或关键句
                    sentences = full_text.split('。')
                    # 取前两句，并加上句号
                    brief_text = '。'.join(sentences[:2]) + '。' if len(sentences) > 1 else full_text
                    # 限制总长度，避免过长
                    brief_text = brief_text[:60] + "..." if len(brief_text) > 60 else brief_text
                    result = f"✨ {CONSTELLATION}：{brief_text}"
                    print(f"✅ 星座运势获取成功 (精简)")
                    return result
                else:
                    print("⚠️ API返回数据中未包含 'text' 或 'summary' 字段")
            else:
                error_msg = data.get('reason', '未知错误')
                print(f"❌ 星座API返回失败 (error_code: {data.get('error_code')}): {error_msg}")
        except Exception as e:
            print(f"❌ 获取星座运势异常: {e}")

        print("⚠️ 星座API调用失败，使用本地模拟数据 (精简)...")
        return self._get_local_horoscope_summary_brief()

    def _get_local_horoscope_summary_brief(self):
        """获取本地星座运势的精简版"""
        # 🔑 精简：只生成一个核心指引和一个幸运小贴士
        general_fortunes_brief = [
            "今天直觉敏锐，相信你的第一感觉。",
            "整体运势不错，保持积极心态。",
            "适合反思和规划未来。",
            "学习能力增强，适合充电。",
            "出门走走，接触新环境带来灵感。",
            "今天是做出决定的好时机。"
        ]

        lucky_tips = [
            "幸运色：粉色",
            "幸运物：小熊玩偶",
            "幸运方向：东方",
            "幸运数字：7",
            "宜：散步、听音乐",
            "忌：熬夜"
        ]

        # 根据日期生成伪随机种子
        today_seed = date.today().toordinal()
        constellation_id = sum(ord(char) for char in CONSTELLATION)
        random.seed(today_seed + constellation_id)

        selected_fortune = random.choice(general_fortunes_brief)
        selected_tip = random.choice(lucky_tips)

        result = f"✨ {CONSTELLATION}：{selected_fortune} {selected_tip}"
        random.seed()  # 重置种子
        return result

    def get_daily_quote(self):
        """获取每日一句 - 使用一言 API"""
        print("正在获取每日一句...")
        try:
            url = "https://v1.hitokoto.cn/"
            response = requests.get(url, timeout=10)
            data = response.json()
            if 'hitokoto' in data:
                quote = data['hitokoto']
                # from字段可能为空
                source = data.get('from', '') or data.get('from_who', '') or '佚名'
                result = f"❝ {quote} ❞\n—— {source}"
                print(f"✅ 每日一句获取成功")
                return result
        except Exception as e:
            print(f"❌ 获取每日一句异常: {e}")
        # 失败时使用备用句子
        fallback_quotes = [
            "生活就像海洋，只有意志坚强的人，才能到达彼岸。—— 马克思",
            "山重水复疑无路，柳暗花明又一村。—— 陆游",
            "宝剑锋从磨砺出，梅花香自苦寒来。",
            "世上无难事，只要肯登攀。—— 毛泽东",
            "爱是理解的别名。—— 泰戈尔"
        ]
        chosen_quote = random.choice(fallback_quotes)
        print(f"⚠️ 每日一句API失败，使用备用句子: {chosen_quote}")
        return chosen_quote

    def send_message(self):
        """发送模板消息"""
        if not TEMPLATE_ID or not USER_ID:
            print("❌ 未配置 WECHAT_TEMPLATE_ID 或 WECHAT_USER_ID")
            return False
        token = self.get_access_token()
        if not token:
            print("❌ 无法获取有效的 access_token")
            return False
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
        # 1. 获取数据
        weather_info = self.get_weather()
        birthday_info = self.calculate_days_until_birthday()
        love_days_info = self.calculate_love_days()
        horoscope_info = self.get_horoscope()  # 调用已修改的方法，现在只返回 summary
        daily_quote = self.get_daily_quote()
        current_date = datetime.now().strftime("%Y年%m月%d日")
        # 存储生成的数据，便于后续使用或调试
        self.generated_data = {
            "date": current_date,
            "city": CITY,
            "weather": weather_info,
            "love_days": love_days_info,
            "birthday_left": birthday_info,
            "constellation": CONSTELLATION,
            "horoscope": horoscope_info,
            "daily_quote": daily_quote,
            "girlfriend_name": GF_NAME
        }
        # 2. 构造消息数据 (字段名需与微信模板一致)
        payload = {
            "touser": USER_ID,
            "template_id": TEMPLATE_ID,
            "data": {
                "date": {"value": current_date, "color": "#173177"},
                "city": {"value": CITY, "color": "#173177"},
                "weather": {"value": weather_info, "color": "#173177"},
                "love_days": {"value": love_days_info, "color": "#FF69B4"},
                "birthday_left": {"value": birthday_info, "color": "#FF4500"},
                "constellation": {"value": CONSTELLATION, "color": "#9370DB"},
                "horoscope": {"value": horoscope_info, "color": "#173177"},  # 现在只显示 summary
                "daily_quote": {"value": daily_quote, "color": "#808080"},
                "girlfriend_name": {"value": GF_NAME, "color": "#FF1493"}
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            res_data = response.json()
            if res_data.get('errcode') == 0:
                print("🎉 消息推送成功!")
                return True
            else:
                print(f"❌ 消息推送失败: {res_data}")
                return False
        except Exception as e:
            print(f"❌ 发送消息时出错: {e}")
            return False

    def run(self):
        """执行推送任务，并返回生成的数据和发送结果"""
        print("--- 开始执行推送任务 ---")
        success = self.send_message()
        if success:
            print("--- 消息推送任务完成 ---")
        else:
            print("--- 消息推送任务失败 ---")

        return {
            "success": success,
            "generated_data": self.generated_data,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    wm = WeChatMessage()
    result = wm.run()
    # 打印结果，便于查看
    print(json.dumps(result, ensure_ascii=False, indent=2))
