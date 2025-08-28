import requests
import os
import json
from datetime import datetime, date
import random
import time
from dotenv import load_dotenv

# --- 读取本地环境变量文件 ---
# 尝试加载本地的 mess.env 文件（用于本地测试）
env_file_path = 'mess.env'
if os.path.exists(env_file_path):
    load_dotenv(env_file_path)
    print(f"✅ 成功加载本地环境变量文件: {env_file_path}")
else:
    print(f"⚠️ 未找到本地环境变量文件: {env_file_path}，将使用系统环境变量")

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
# --- 新增：天行数据星座 API Key ---
TIANAPI_KEY = os.getenv('TIANAPI_KEY')  # 请务必设置此环境变量


class WeChatMessage:
    def __init__(self):
        self.access_token = None
        self.token_expire_time = 0
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
        """获取天气信息 - 使用高德天气 API"""
        print("正在获取天气信息...")
        if not AMAP_KEY:
            print("⚠️ 未配置高德地图 API Key (AMAP_KEY)，使用本地天气数据")
            return self._get_local_weather()

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
                return self._get_local_weather()

            # 2. 通过 adcode 获取天气信息
            weather_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={adcode}&key={AMAP_KEY}&extensions=base"
            weather_response = requests.get(weather_url, timeout=10)
            weather_data = weather_response.json()

            if weather_data.get('status') == '1' and weather_data.get('lives'):
                live_weather = weather_data['lives'][0]
                weather = live_weather['weather']
                temperature = live_weather['temperature']
                humidity = live_weather['humidity']
                wind_direction = live_weather['winddirection']
                wind_power = live_weather['windpower']

                tip = self._get_weather_tip(weather)
                result = f"🌤️ {weather}, {temperature}°C (湿度{humidity}%, {wind_direction}风{wind_power}级) | {tip}"
                print(f"✅ 天气获取成功: {result}")
                return result
            else:
                print(f"❌ 获取天气信息失败: {weather_data}")
                return self._get_local_weather()

        except Exception as e:
            print(f"❌ 获取天气信息异常: {e}")
            return self._get_local_weather()

    def _get_local_weather(self):
        """获取本地天气数据"""
        # 根据月份生成合理的天气
        now = datetime.now()
        month = now.month
        day_temp = random.randint(15, 35)
        night_temp = random.randint(5, day_temp - 5)

        if month in [12, 1, 2]:  # 冬季
            weathers = [
                f"❄️ 晴 {night_temp}°C~{day_temp}°C | 冬天来了，记得穿暖暖",
                f"🌨️ 小雪 {night_temp}°C~{day_temp}°C | 下雪啦，小心路滑"
            ]
        elif month in [3, 4, 5]:  # 春季
            weathers = [
                f"🌸 晴 {night_temp}°C~{day_temp}°C | 春暖花开，适合散步",
                f"🌧️ 小雨 {night_temp}°C~{day_temp}°C | 春雨绵绵，带把伞吧"
            ]
        elif month in [6, 7, 8]:  # 夏季
            weathers = [
                f"🌞 晴 {night_temp}°C~{day_temp}°C | 热浪来袭，注意防暑",
                f"⛈️ 雷阵雨 {night_temp}°C~{day_temp}°C | 午后可能有雨，带伞出门"
            ]
        else:  # 秋季
            weathers = [
                f"🍂 晴 {night_temp}°C~{day_temp}°C | 秋高气爽，很舒服呢",
                f"🌫️ 多云 {night_temp}°C~{day_temp}°C | 云淡风轻，适合郊游"
            ]

        chosen_weather = random.choice(weathers)
        print(f"⚠️ 使用本地天气数据: {chosen_weather}")
        return chosen_weather

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
        """获取星座运势 - 使用天行数据 API"""
        print("正在获取星座运势...")
        if not TIANAPI_KEY:
            print("⚠️ 未配置天行数据 API Key (TIANAPI_KEY)，使用本地模拟数据")
            return self._get_local_horoscope_summary()

        try:
            # 使用天行数据提供的星座运势 API
            url = "https://apis.tianapi.com/star/index"
            params = {
                'key': TIANAPI_KEY,  # API Key
                'astro': CONSTELLATION  # 星座名称
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            print(f"星座API返回原始数据: {data}")  # 调试信息

            # 检查API返回是否成功
            if data.get('code') == 200 and 'result' in data and 'list' in data['result']:
                horoscope_list = data['result']['list']
                print(f"星座运势列表: {horoscope_list}")  # 调试信息

                # 查找"今日概述"的内容
                today_summary = ""
                for item in horoscope_list:
                    if item.get('type') == '今日概述':
                        today_summary = item.get('content', '')
                        break

                # 如果没有找到"今日概述"，则组合多个条目
                if not today_summary and horoscope_list:
                    summary_parts = []
                    for item in horoscope_list:
                        item_type = item.get('type', '')
                        content = item.get('content', '')
                        if content and item_type != '综合指数':  # 跳过综合指数
                            summary_parts.append(f"{item_type}: {content}")

                    today_summary = "  ".join(summary_parts)

                if today_summary:
                    result = f"✨ {CONSTELLATION}今日运势：{today_summary}"
                    print(f"✅ 星座运势获取成功: {result}")
                    return result
                else:
                    print("⚠️ API返回数据中未包含有效的内容字段")

            else:
                error_msg = data.get('msg', '未知错误')
                print(f"❌ 星座API返回失败 (code: {data.get('code')}): {error_msg}")

        except Exception as e:
            print(f"❌ 获取星座运势异常: {e}")

        # 如果API调用失败或出错，回退到本地模拟
        print("⚠️ 星座API调用失败，使用本地模拟数据...")
        return self._get_local_horoscope_summary()

    def _get_local_horoscope_summary(self):
        """获取本地星座运势的 summary 部分 - 作为备用方案"""
        # 定义一些通用的运势前缀，让结果听起来更专业
        prefixes = [
            f"✨ {CONSTELLATION}今日运势：",
            f"🔮 {CONSTELLATION}专属占卜：",
            f"⭐ {CONSTELLATION}今日指引：",
            f"💫 {CONSTELLATION}能量播报：",
        ]
        prefix = random.choice(prefixes)

        # 定义按运势类型分类的句子
        love_fortunes = [
            "单身者有机会在社交场合遇到心仪的对象，保持开放的心态。",
            "有伴侣的人今天适合安排一次浪漫的约会，增进感情。",
            "沟通是关键，多倾听对方的想法，避免不必要的误会。",
            "感受到爱意的流动，一个小小的举动就能让对方感到幸福。",
            "情感运势稳定，适合与爱人分享内心深处的想法。",
            "可能会收到来自异性的邀请，不妨尝试接受。"
        ]
        work_fortunes = [
            "工作中可能会遇到挑战，但你的创意和努力将得到认可。",
            "团队合作非常重要，多与同事交流，集思广益。",
            "今天适合处理积压的事务，效率会很高。",
            "可能会有新的项目或机会出现，保持警觉。",
            "避免在细节上过于纠结，把握大局更为重要。",
            "学习新技能的好时机，投资自己总是值得的。"
        ]
        money_fortunes = [
            "财运平稳，适合制定理财计划。",
            "可能会有意外的小收入，比如红包或退款。",
            "花钱要理性，避免冲动消费。",
            "投资方面需要谨慎，多做研究再做决定。",
            "正财稳定，偏财运也不错，有机会通过副业增收。",
            "记账是个好习惯，能帮你更好地掌控财务状况。"
        ]
        health_fortunes = [
            "注意劳逸结合，避免过度劳累。",
            "多喝水，多吃水果蔬菜，保持身体健康。",
            "适合进行一些轻松的运动，如散步或瑜伽。",
            "情绪对健康影响很大，保持乐观的心态。",
            "可能会感到有些疲惫，早点休息是不错的选择。",
            "关注身体发出的信号，不适时及时调整。"
        ]
        general_fortunes = [
            "今天你的直觉很敏锐，相信第一感觉。",
            "整体运势不错，保持积极的心态会带来更多好运。",
            "可能会遇到需要做决定的时刻，深思熟虑后行动。",
            "学习能力增强，适合给自己充电。",
            "出门走走，接触新环境会带来灵感。",
            "今天适合反思和规划，为未来做好准备。"
        ]

        # 根据当前日期生成一个"伪随机"种子，使得同一天的运势相对固定
        today_seed = date.today().toordinal()
        # 简单根据星座名称生成一个基础ID
        constellation_id = sum(ord(char) for char in CONSTELLATION)
        random.seed(today_seed + constellation_id)

        # 为每个类别随机选择1条
        selected_love = random.choice(love_fortunes)
        selected_work = random.choice(work_fortunes)
        selected_money = random.choice(money_fortunes)
        selected_health = random.choice(health_fortunes)
        selected_general = random.choice(general_fortunes)

        # 组合运势信息 (模拟 summary 的感觉)
        horoscope_summary = f"{selected_general} {selected_love} {selected_work} {selected_money} {selected_health}"

        # 添加一些可爱的结尾
        endings = [
            "愿你今天被幸福填满！",
            "带着微笑开启新的一天吧！",
            "宇宙与你同在，加油！",
            "每一天都是限量版，好好珍惜！",
            "你的存在就是最好的礼物！"
        ]
        horoscope_summary += " " + random.choice(endings)

        result = prefix + horoscope_summary
        # 重置随机种子，避免影响其他部分
        random.seed()
        return result

    def get_daily_quote(self):
        """获取每日一句 - 使用天行数据对话 API"""
        print("正在获取每日一句...")
        if not TIANAPI_KEY:
            print("⚠️ 未配置天行数据 API Key (TIANAPI_KEY)，使用一言API")
            return self._get_hitokoto_quote()

        try:
            # 使用天行数据提供的对话 API
            url = "https://apis.tianapi.com/dialogue/index"
            params = {
                'key': TIANAPI_KEY  # API Key
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            print(f"每日一句API返回原始数据: {data}")  # 调试信息

            # 检查API返回是否成功
            if data.get('code') == 200 and 'result' in data:
                quote_data = data['result']

                # 提取对话内容和来源
                dialogue = quote_data.get('dialogue', '')
                source = quote_data.get('source', '')

                if dialogue:
                    # 如果有来源信息，也一并显示
                    if source:
                        result = f"❝ {dialogue} ❞\n—— {source}"
                    else:
                        result = f"❝ {dialogue} ❞"
                    print(f"✅ 每日一句获取成功: {result}")
                    return result
                else:
                    print("⚠️ API返回数据中未包含对话内容")

            else:
                error_msg = data.get('msg', '未知错误')
                print(f"❌ 每日一句API返回失败 (code: {data.get('code')}): {error_msg}")

        except Exception as e:
            print(f"❌ 获取每日一句异常: {e}")

        # 如果API调用失败或出错，回退到一言API
        print("⚠️ 每日一句API调用失败，使用一言API...")
        return self._get_hitokoto_quote()

    def _get_hitokoto_quote(self):
        """获取一言API的句子作为备选方案"""
        try:
            url = "https://v1.hitokoto.cn/"
            response = requests.get(url, timeout=10)
            data = response.json()

            if 'hitokoto' in data:
                quote = data['hitokoto']
                # from字段可能为空
                source = data.get('from', '') or data.get('from_who', '') or '佚名'
                result = f"❝ {quote} ❞\n—— {source}"
                print(f"✅ 一言API获取成功: {result}")
                return result
        except Exception as e:
            print(f"❌ 获取一言API异常: {e}")

        # 失败时使用备用句子
        fallback_quotes = [
            "生活就像海洋，只有意志坚强的人，才能到达彼岸。—— 马克思",
            "山重水复疑无路，柳暗花明又一村。—— 陆游",
            "宝剑锋从磨砺出，梅花香自苦寒来。",
            "世上无难事，只要肯登攀。—— 毛泽东",
            "爱是理解的别名。—— 泰戈尔"
        ]
        chosen_quote = random.choice(fallback_quotes)
        print(f"⚠️ 一言API失败，使用备用句子: {chosen_quote}")
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
        """执行推送任务"""
        print("--- 开始执行推送任务 ---")

        # 直接发送消息
        success = self.send_message()

        if success:
            print("--- 消息推送任务完成 ---")
        else:
            print("--- 消息推送任务失败 ---")


if __name__ == "__main__":
    wm = WeChatMessage()
    wm.run()
    # 如果需要定时任务，可以使用 APScheduler
    # from apscheduler.schedulers.blocking import BlockingScheduler
    # scheduler = BlockingScheduler()
    # scheduler.add_job(wm.run, 'cron', hour=8, minute=0) # 每天8点执行
    # print("定时任务已启动...")
    # try:
    #     scheduler.start()
    # except KeyboardInterrupt:
    #     print("定时任务已停止。")
    #     scheduler.shutdown()
