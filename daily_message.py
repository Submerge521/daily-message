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
CITY = os.getenv('CITY', '广州')  # 默认城市
BIRTHDAY = os.getenv('BIRTHDAY', '02-27')  # 格式: MM-DD
RELATIONSHIP_DATE = os.getenv('RELATIONSHIP_DATE', '2025-08-18')  # 格式: YYYY-MM-DD
GF_NAME = os.getenv('GF_NAME', '小睿')
CONSTELLATION = os.getenv('CONSTELLATION', '白羊座')  # 星座名称

# --- 高德地图 API Key ---
AMAP_KEY = os.getenv('AMAP_KEY')  # 必须配置才能获取真实天气

# # --- 聚合数据星座 API Key ---
# JUHE_CONSTELLATION_KEY = os.getenv('JUHE_CONSTELLATION_KEY')  # 可选，若无则用本地模拟


class WeChatMessage:
    def __init__(self):
        self.access_token = None
        self.token_expire_time = 0
        self.generated_data = {}  # 存储生成的数据，用于调试和返回
        self.init_relationship_date()

    def init_relationship_date(self):
        """初始化恋爱开始日期"""
        try:
            self.relationship_start = datetime.strptime(RELATIONSHIP_DATE, '%Y-%m-%d').date()
        except Exception as e:
            print(f"恋爱日期格式错误，使用默认值: {e}")
            self.relationship_start = date(2023, 1, 1)

    def get_access_token(self):
        """获取 access_token，带缓存与重试机制"""
        if not APPID or not APPSECRET:
            print("❌ 未配置 WECHAT_APPID 或 WECHAT_APPSECRET")
            return None

        # 检查是否已有有效 token
        now = datetime.now().timestamp()
        if self.access_token and now < self.token_expire_time:
            return self.access_token

        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
        max_retries = 3
        for i in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    # 提前 300 秒过期，避免临界问题
                    self.token_expire_time = now + data['expires_in'] - 300
                    print("✅ 获取 access_token 成功")
                    return self.access_token
                else:
                    print(f"❌ 获取 access_token 失败: {data}")
            except Exception as e:
                print(f"❌ 请求 access_token 异常 (第 {i + 1} 次): {e}")
                if i < max_retries - 1:
                    time.sleep(2)
        return None

    def get_weather(self):
        """获取天气信息（精简版）"""
        print("正在获取天气信息...")
        if not AMAP_KEY:
            print("⚠️ 未配置 AMAP_KEY，使用本地模拟天气")
            return self._get_local_weather_summary()

        try:
            # 获取城市 adcode
            geo_url = f"https://restapi.amap.com/v3/geocode/geo?address={CITY}&key={AMAP_KEY}"
            geo_response = requests.get(geo_url, timeout=10)
            geo_data = geo_response.json()

            if geo_data.get('status') != '1' or not geo_data.get('geocodes'):
                print(f"❌ 地理编码失败: {geo_data}")
                return self._get_local_weather_summary()

            adcode = geo_data['geocodes'][0]['adcode']
            print(f"✅ 城市 {CITY} 的 adcode: {adcode}")

            # 获取实时天气
            weather_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={AMAP_KEY}&extensions=base"
            weather_response = requests.get(weather_url, timeout=10)
            weather_data = weather_response.json()

            if weather_data.get('status') == '1' and weather_data.get('lives'):
                live = weather_data['lives'][0]
                weather = live['weather']
                temp = live['temperature']
                tip = self._get_weather_tip(weather)
                result = f"{weather} {temp}°C | {tip}"
                print(f"✅ 天气获取成功: {result}")
                return result
            else:
                print(f"❌ 天气接口返回失败: {weather_data}")
                return self._get_local_weather_summary()

        except Exception as e:
            print(f"❌ 获取天气异常: {e}")
            return self._get_local_weather_summary()

    def _get_local_weather_summary(self):
        """本地模拟天气（精简）"""
        now = datetime.now()
        month = now.month
        temp = random.randint(15, 35)
        tips = {
            12: "冬天来了，记得穿暖暖",
            1: "新年快乐，注意保暖",
            2: "春寒料峭，多穿点哦",
            3: "春暖花开，适合散步",
            4: "微风拂面，心情很好",
            5: "阳光正好，适合出游",
            6: "热浪来袭，注意防暑",
            7: "夏日炎炎，记得补水",
            8: "高温持续，空调别开太低",
            9: "秋高气爽，很舒服呢",
            10: "金秋时节，落叶很美",
            11: "凉风渐起，早晚添衣"
        }
        weather = random.choice(["晴", "多云", "阴"])
        tip = tips.get(month, "天气多变，照顾好自己")
        result = f"{weather} {temp}°C | {tip}"
        print(f"⚠️ 使用本地天气: {result}")
        return result

    def _get_weather_tip(self, weather_type):
        """根据天气返回提示语"""
        tips = {
            "晴": "阳光很好，记得涂防晒霜哦~",
            "多云": "云朵飘飘，心情也会变好",
            "阴": "阴天也要保持好心情呀",
            "雨": "记得带伞，不想你淋雨",
            "雪": "下雪啦！要穿暖暖的",
            "雾": "雾天注意安全，慢慢走",
            "雷阵雨": "雷雨天，注意安全",
            "小雨": "毛毛雨，带把小伞更贴心",
            "中雨": "雨有点大，记得带伞",
            "大雨": "雨很大，注意安全",
            "暴雨": "暴雨预警，请注意防范！",
        }
        return tips.get(weather_type, "天气多变，要照顾好自己哦")

    def calculate_days_until_birthday(self):
        """计算距离生日还有几天"""
        try:
            today = date.today()
            month, day = map(int, BIRTHDAY.split('-'))
            year = today.year
            # 处理 2月29日
            if month == 2 and day == 29:
                if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                    birthday_this_year = date(year, 2, 29)
                else:
                    birthday_this_year = date(year, 3, 1)
            else:
                birthday_this_year = date(year, month, day)

            if today > birthday_this_year:
                year += 1
                if month == 2 and day == 29:
                    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                        next_birthday = date(year, 2, 29)
                    else:
                        next_birthday = date(year, 3, 1)
                else:
                    next_birthday = date(year, month, day)
            else:
                next_birthday = birthday_this_year

            days_left = (next_birthday - today).days
            if days_left == 0:
                return "🎉 今天是生日！生日快乐我的宝贝！"
            elif days_left == 1:
                return "🌟 明天生日！已经准备好惊喜啦~"
            elif days_left < 7:
                return f"🎂 还有{days_left}天！超级期待！"
            elif days_left < 30:
                return f"💝 还有{days_left}天，每天都在想你"
            else:
                return f"🗓️ 还有{days_left}天，但爱你的心从不停止"
        except Exception as e:
            print(f"生日计算出错: {e}")
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
            print(f"恋爱天数计算失败: {e}")
            return "💓 每一天都值得珍惜"

    def get_horoscope(self):
        """获取星座运势（精简总结版）"""
        print("正在获取星座运势...")
        # if not JUHE_CONSTELLATION_KEY:
        #     print("⚠️ 未配置星座 API Key，使用本地模拟")
        #     return self._get_local_horoscope_summary_brief()

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
                summary = data['result'].get('summary', '')
                if len(summary) > 60:
                    sentences = summary.split('。')
                    brief = '。'.join(sentences[:2]) + '。' if len(sentences) > 1 else summary[:60] + "..."
                else:
                    brief = summary
                result = brief[:70] + "..." if len(brief) > 70 else brief
                print("✅ 星座运势获取成功（已精简）")
                return result
            else:
                print(f"❌ 星座API失败: {data.get('reason', '未知错误')}")
        except Exception as e:
            print(f"❌ 获取星座运势异常: {e}")

        print("⚠️ 使用本地星座运势")
        return self._get_local_horoscope_summary_brief()

    def _get_local_horoscope_summary_brief(self):
        """本地模拟精简版星座运势"""
        fortunes = [
            "今天直觉敏锐，相信你的第一感觉。",
            "整体运势不错，保持积极心态。",
            "适合反思和规划未来。",
            "学习能力增强，适合充电。",
            "出门走走，接触新环境带来灵感。",
            "今天是做出决定的好时机。",
            "人际和谐，容易获得帮助。",
            "财运小升，适合记账理财。"
        ]
        tips = [
            "幸运色：粉色",
            "幸运物：小熊玩偶",
            "幸运方向：东方",
            "幸运数字：7",
            "宜：散步、听音乐",
            "忌：熬夜"
        ]
        today_seed = date.today().toordinal()
        constellation_id = sum(ord(c) for c in CONSTELLATION)
        random.seed(today_seed + constellation_id)
        fortune = random.choice(fortunes)
        tip = random.choice(tips)
        result = f"{fortune} {tip}"
        random.seed()  # 重置随机种子
        return result

    def get_daily_quote(self):
        """获取每日一句"""
        print("正在获取每日一句...")
        try:
            url = "https://v1.hitokoto.cn/"
            response = requests.get(url, timeout=10)
            data = response.json()
            if 'hitokoto' in data:
                quote = data['hitokoto'].strip()
                source = data.get('from', '') or data.get('from_who', '') or '佚名'
                result = f"❝ {quote} ❞ —— {source}"
                print("✅ 每日一句获取成功")
                return result
        except Exception as e:
            print(f"❌ 获取每日一句失败: {e}")

        # 备用语录
        fallbacks = [
            "山重水复疑无路，柳暗花明又一村。—— 陆游",
            "生活不止眼前的苟且，还有诗和远方。—— 高晓松",
            "愿你一生努力，一生被爱。"
        ]
        result = random.choice(fallbacks)
        print(f"⚠️ 使用备用句子: {result}")
        return result

    def send_message(self):
        """发送模板消息"""
        if not all([APPID, APPSECRET, TEMPLATE_ID, USER_ID]):
            print("❌ 缺少必要配置，请检查环境变量")
            return False

        token = self.get_access_token()
        if not token:
            print("❌ 无法获取 access_token")
            return False

        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"

        # 获取所有数据
        current_date = datetime.now().strftime("%Y年%m月%d日")
        weather_info = self.get_weather()
        love_days_info = self.calculate_love_days()
        birthday_info = self.calculate_days_until_birthday()
        horoscope_info = self.get_horoscope()
        daily_quote = self.get_daily_quote()

        # 存储生成的数据（用于调试或记录）
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

        # 构造模板消息数据（字段名必须与模板一致）
        payload = {
            "touser": USER_ID,
            "template_id": TEMPLATE_ID,
            "data": {
                "girlfriend_name": {"value": GF_NAME, "color": "#FF1493"},
                "date": {"value": current_date, "color": "#173177"},
                "city": {"value": CITY, "color": "#173177"},
                "weather": {"value": weather_info, "color": "#173177"},
                "love_days": {"value": love_days_info, "color": "#FF69B4"},
                "birthday_left": {"value": birthday_info, "color": "#FF4500"},
                "constellation": {"value": CONSTELLATION, "color": "#9370DB"},
                "horoscope": {"value": horoscope_info, "color": "#173177"},
                "daily_quote": {"value": daily_quote, "color": "#808080"}
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            res = response.json()
            if res.get('errcode') == 0:
                print("🎉 模板消息发送成功！")
                return True
            else:
                print(f"❌ 发送失败: {res}")
                return False
        except Exception as e:
            print(f"❌ 发送请求异常: {e}")
            return False

    def run(self):
        """运行主流程"""
        print("=== 开始执行每日推送任务 ===")
        success = self.send_message()
        result = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "generated_data": self.generated_data
        }
        print("=== 推送任务结束 ===")
        return result


# --- 主程序入口 ---
if __name__ == "__main__":
    wechat = WeChatMessage()
    result = wechat.run()
    # 输出结果（可用于日志或调试）
    print(json.dumps(result, ensure_ascii=False, indent=2))
