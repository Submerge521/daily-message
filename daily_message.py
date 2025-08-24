import requests
import os
import json
from datetime import datetime, date, timedelta
import random
import time

# 从环境变量获取配置
APPID = os.getenv('WECHAT_APPID')
APPSECRET = os.getenv('WECHAT_APPSECRET')
TEMPLATE_ID = os.getenv('WECHAT_TEMPLATE_ID')
USER_ID = os.getenv('WECHAT_USER_ID')
CITY = os.getenv('CITY', '广州')
BIRTHDAY = os.getenv('BIRTHDAY', '02-16')  # 格式: MM-DD
RELATIONSHIP_DATE = os.getenv('RELATIONSHIP_DATE', '2025-08-18')  # 格式: YYYY-MM-DD
GF_NAME = os.getenv('GF_NAME', '小睿')
CONSTELLATION = os.getenv('CONSTELLATION', '水瓶座')  # 星座名称

class WeChatMessage:
    def __init__(self):
        self.access_token = None
        self.token_expire_time = 0
        # 初始化恋爱天数计算
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
                print(f"❌ 获取access_token异常 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        return None
    
    def get_weather(self):
        """获取天气信息 - 确保一定有返回"""
        print("正在获取天气信息...")
        
        # 尝试多个天气API
        weather_apis = [
            self._try_wttr_weather,
            self._try_vvhan_weather,
            self._try_tianqi_weather
        ]
        
        for api_func in weather_apis:
            try:
                result = api_func()
                if result and result != "暂无天气信息":
                    print(f"✅ 天气获取成功: {result}")
                    return result
            except Exception as e:
                print(f"天气API尝试失败: {e}")
                continue
        
        # 所有API都失败时使用智能本地天气
        print("⚠️ 所有天气API失败，使用本地天气数据")
        return self._get_local_weather()
    
    def _try_wttr_weather(self):
        """尝试wttr.in天气API"""
        try:
            url = f"http://wttr.in/{CITY}?format=%C+%t"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                weather = response.text.strip()
                return f"🌤️ {weather} | 出门记得看看天空哦~"
        except:
            return None
    
    def _try_vvhan_weather(self):
        """尝试vvhan天气API"""
        try:
            url = f"https://api.vvhan.com/api/weather?city={CITY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                info = data['info']
                weather_type = info['type']
                temp_range = f"{info['low']}°C~{info['high']}°C"
                tip = self._get_weather_tip(weather_type)
                return f"🌤️ {weather_type} {temp_range} | {tip}"
        except:
            return None
    
    def _try_tianqi_weather(self):
        """尝试其他天气API"""
        try:
            # 另一个备选天气API
            url = f"https://api.qqsuu.cn/api/dm-tianqi?city={CITY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('code') == 200:
                weather = data['data']['weather']
                temp = data['data']['temp']
                return f"🌤️ {weather} {temp} | 天气变化，注意身体~"
        except:
            return None
    
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
                f"🌨️ 雪 {night_temp}°C~{day_temp}°C | 下雪啦，小心路滑"
            ]
        elif month in [3, 4, 5]:  # 春季
            weathers = [
                f"🌸 晴 {night_temp}°C~{day_temp}°C | 春暖花开，适合散步",
                f"🌧️ 小雨 {night_temp}°C~{day_temp}°C | 春雨绵绵，带把伞吧"
            ]
        elif month in [6, 7, 8]:  # 夏季
            weathers = [
                f"🌞 晴 {night_temp}°C~{day_temp}°C | 热浪来袭，注意防暑",
                f"⛈️ 雷阵雨 {night_temp}°C~{day_temp}°C | 可能有雨，带伞出门"
            ]
        else:  # 秋季
            weathers = [
                f"🍂 晴 {night_temp}°C~{day_temp}°C | 秋高气爽，很舒服呢",
                f"🌫️ 多云 {night_temp}°C~{day_temp}°C | 云淡风轻，适合郊游"
            ]
        
        return random.choice(weathers)
    
    def _get_weather_tip(self, weather_type):
        """根据天气类型获取提示"""
        tips = {
            "晴": "阳光很好，记得防晒哦~",
            "多云": "云朵飘飘，心情也会变好",
            "阴": "阴天也要保持好心情呀",
            "雨": "记得带伞，不想你淋雨",
            "雪": "下雪啦！要穿暖暖的",
            "雾": "雾天注意安全，慢慢走"
        }
        return tips.get(weather_type, "要照顾好自己哦")
    
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
                if month == 2 and day == 29 and not (next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0)):
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
        """获取星座运势 - 确保一定有返回"""
        print("正在获取星座运势...")
        
        # 尝试多个星座API
        horoscope_apis = [
            lambda: self._try_vvhan_horoscope(CONSTELLATION),
            lambda: self._try_81chart_horoscope(CONSTELLATION),
            lambda: self._try_astrology_horoscope(CONSTELLATION)
        ]
        
        for api_func in horoscope_apis:
            try:
                result = api_func()
                if result and result != "今天会是美好的一天":
                    print(f"✅ 星座获取成功: {result}")
                    return result
            except Exception as e:
                print(f"星座API尝试失败: {e}")
                continue
        
        # 所有API都失败时使用本地运势
        print("⚠️ 所有星座API失败，使用本地星座数据")
        return self._get_local_horoscope()
    
    def _try_vvhan_horoscope(self, constellation):
        """尝试vvhan星座API"""
        constellation_map = {
            "白羊座": "aries", "金牛座": "taurus", "双子座": "gemini",
            "巨蟹座": "cancer", "狮子座": "leo", "处女座": "virgo",
            "天秤座": "libra", "天蝎座": "scorpio", "射手座": "sagittarius",
            "摩羯座": "capricorn", "水瓶座": "aquarius", "双鱼座": "pisces"
        }
        
        en_constellation = constellation_map.get(constellation, "pisces")
        
        try:
            url = f"https://api.vvhan.com/api/horoscope?type={en_constellation}&time=today"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                content = data['data'].get('content', '')
                if content:
                    return f"✨ {constellation}今天运势很棒！{content[:45]}..."
        except:
            return None
    
    def _try_81chart_horoscope(self, constellation):
        """尝试81chart星座API"""
        try:
            url = f"https://api.81chart.com/horoscope/daily?constellation={constellation}&lang=zh-CN"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('code') == 0:
                fortune = data['data']['fortune']
                return f"✨ {constellation}今日{fortune}，感情方面有小惊喜..."
        except:
            return None
    
    def _try_astrology_horoscope(self, constellation):
        """尝试另一个星座API"""
        try:
            url = f"https://api.astrologyapi.com/v1/daily_horoscope/{constellation}/today"
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Basic YXBpLWFzdGlyb2x5YXBpOjEyMzQ1Ng=="  # 示例授权，可能需要替换
            }
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()
            if 'horoscope_data' in data:
                return f"✨ {constellation}今天{data['horoscope_data'][:40]}..."
        except:
            return None
    
    def _get_local_horoscope(self):
        """获取本地星座运势"""
        horoscopes = [
            f"✨ {CONSTELLATION}今天运势很棒！感情方面会有小惊喜，保持开放的心态~",
            f"💫 {CONSTELLATION}今天适合创意工作，你的直觉很准，相信自己的感觉吧！",
            f"🌈 {CONSTELLATION}整体运势不错，可能会遇到意想不到的好事，保持微笑~",
            f"🎯 {CONSTELLATION}是制定计划的好时机，你的梦想正在一步步实现呢",
            f"❤️ {CONSTELLATION}爱情运势佳，适合表达心意，对方会被你的真诚打动"
        ]
        return random.choice(horoscopes)
    
    def get_daily_tip(self):
        """获取每日提醒 - 确保一定有返回"""
        print("正在获取每日提醒...")
        
        # 尝试多个提醒API
        tip_apis = [
            self._try_btstu_tip,
            self._try_mcloc_tip,
            self._try_local_tip
        ]
        
        for api_func in tip_apis:
            try:
                result = api_func()
                if result:
                    print(f"✅ 提醒获取成功: {result}")
                    return result
            except Exception as e:
                print(f"提醒API尝试失败: {e}")
                continue
        
        # 最终备用
        return "💡 记得今天也要开心哦~"
    
    def _try_btstu_tip(self):
        """尝试btstu提醒API"""
        try:
            url = "https://api.btstu.cn/tips/api.php?charset=utf-8"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return f"💡 {response.text.strip()}"
        except:
            return None
    
    def _try_mcloc_tip(self):
        """尝试mcloc提醒API"""
        try:
            url = "https://api.mcloc.cn/tips/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return f"💡 {response.text.strip()}"
        except:
            return None
    
    def _try_local_tip(self):
        """本地提醒"""
        tips = [
            "记得喝够8杯水，保持水润润的~",
            "今天也要好好吃饭，不要饿着自己",
            "保持微笑，你的笑容是最美的风景",
            "适当休息，别让自己太累了",
            "出门前检查物品，别忘带东西哦",
            "天气变化，注意增减衣物",
            "工作再忙也要记得放松一下呀",
            "今天也要运动一下，保持健康"
        ]
        return f"💡 {random.choice(tips)}"
    
    def get_sweet_words(self):
        """获取情话 - 确保一定有返回"""
        print("正在获取情话...")
        
        # 尝试多个情话API
        sweet_apis = [
            self._try_btstu_sweet,
            self._try_mcloc_sweet,
            self._try_vvhan_sweet
        ]
        
        for api_func in sweet_apis:
            try:
                result = api_func()
                if result:
                    print(f"✅ 情话获取成功: {result}")
                    return result
            except Exception as e:
                print(f"情话API尝试失败: {e}")
                continue
        
        # 所有API都失败时使用本地情话
        print("⚠️ 所有情话API失败，使用本地情话数据")
        return self._get_local_sweet_words()
    
    def _try_btstu_sweet(self):
        """尝试btstu情话API"""
        try:
            url = "https://api.btstu.cn/saylove/api.php?charset=utf-8"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return f"💌 {response.text.strip()}"
        except:
            return None
    
    def _try_mcloc_sweet(self):
        """尝试mcloc情话API"""
        try:
            url = "https://api.mcloc.cn/love/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return f"💌 {response.text.strip()}"
        except:
            return None
    
    def _try_vvhan_sweet(self):
        """尝试vvhan情话API"""
        try:
            url = "https://api.vvhan.com/api/love"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                return f"💌 {data.get('ishan', '')}"
        except:
            return None
    
    def _get_local_sweet_words(self):
        """获取本地情话"""
        sweet_words = [
            f"🐰 今天也是想扑进{GF_NAME}怀里的一天~",
            f"🌟 {GF_NAME}是我生命中最亮的星星",
            f"💕 爱{GF_NAME}是我做过最正确的决定",
            f"🍬 和{GF_NAME}在一起的每一天都甜甜蜜蜜",
            f"🌻 {GF_NAME}是我的小太阳，温暖我的心",
            f"🎯 我的目标就是让{GF_NAME}每天都开心",
            f"🌈 遇见你是我最大的幸运，{GF_NAME}",
            f"🎁 {GF_NAME}就是我最好的礼物"
        ]
        return random.choice(sweet_words)
    
    def get_greeting(self):
        """获取顶部问候语"""
        hour = datetime.now().hour
        
        if 5 <= hour < 10:
            greetings = [
                f"🌞 早安{GF_NAME}！新的一天开始啦~",
                f"☀️ 早上好{GF_NAME}，今天也是爱你的一天",
                f"🌅 {GF_NAME}早安，愿你今天有个好心情"
            ]
        elif 10 <= hour < 14:
            greetings = [
                f"🌞 午安{GF_NAME}！记得好好吃饭哦~",
                f"🍱 {GF_NAME}中午好，今天也要元气满满",
                f"☀️ 中午好{GF_NAME}，休息一下吧"
            ]
        elif 14 <= hour < 18:
            greetings = [
                f"🌤️ 下午好{GF_NAME}！工作再忙也要注意休息~",
                f"☕ {GF_NAME}下午好，喝杯茶放松一下吧",
                f"🌞 午后好{GF_NAME}，愿你有个轻松的下午"
            ]
        else:
            greetings = [
                f"🌙 晚安{GF_NAME}！今天辛苦了~",
                f"✨ 晚上好{GF_NAME}，好好享受夜晚时光吧",
                f"🌌 {GF_NAME}晚安，做个甜甜的梦"
            ]
        
        return random.choice(greetings)
    
    def get_remark(self):
        """获取底部备注"""
        remarks = [
            f"💖 永远爱你的我 | 🌈 每一天都因{GF_NAME}而美好",
            f"🤗 想你的每一刻 | 🎯 今天也要加油哦",
            f"🐾 你的专属温暖 | 🌟 期待与你的每一天"
        ]
        return random.choice(remarks)
    
    def send_message(self):
        """发送微信模板消息，带重试机制"""
        print("开始准备消息内容...")
        
        # 检查必要配置
        if not all([APPID, APPSECRET, TEMPLATE_ID, USER_ID]):
            print("❌ 微信配置信息不完整")
            return False
        
        # 获取access_token
        access_token = self.get_access_token()
        if not access_token:
            return False
        
        # 准备消息数据
        greeting = self.get_greeting()
        weather = self.get_weather()
        birthday_countdown = self.calculate_days_until_birthday()
        love_days = self.calculate_love_days()
        horoscope = self.get_horoscope()
        sweet_words = self.get_sweet_words()
        daily_tip = self.get_daily_tip()
        remark = self.get_remark()
        
        # 获取当前日期和星期
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        current_date = datetime.now().strftime('%Y年%m月%d日')
        current_weekday = f"星期{weekdays[datetime.now().weekday()]}"
        
        # 构建模板数据，确保与微信模板中的字段对应
        template_data = {
            "touser": USER_ID,
            "template_id": TEMPLATE_ID,
            "url": "https://github.com",  # 点击消息跳转的URL
            "data": {
                "greeting": {
                    "value": greeting,
                    "color": "#FF6B9D"  # 粉色
                },
                "date": {
                    "value": current_date,
                    "color": "#5B8FF9"  # 蓝色
                },
                "weekday": {
                    "value": current_weekday,
                    "color": "#5B8FF9"  # 蓝色
                },
                "birthday": {
                    "value": f"破壳日：{birthday_countdown}",
                    "color": "#FF9D4D"  # 橙色
                },
                "love_days": {
                    "value": love_days,
                    "color": "#FF6B6B"  # 红色
                },
                "weather": {
                    "value": f"看看天气：{weather}",
                    "color": "#30BF78"  # 绿色
                },
                "horoscope": {
                    "value": f"星座：{horoscope}",
                    "color": "#9A5FE8"  # 紫色
                },
                "sweet_words": {
                    "value": f"想说：{sweet_words}",
                    "color": "#FF6B6B"  # 红色
                },
                "daily_tip": {
                    "value": f"今天的tip：{daily_tip}",
                    "color": "#FFC53D"  # 黄色
                },
                "remark": {
                    "value": remark,
                    "color": "#FF85C0"  # 浅粉色
                }
            }
        }
        
        print("消息内容准备完成，开始发送...")
        
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
        max_retries = 2
        retry_delay = 3  # 秒
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=template_data, timeout=10)
                result = response.json()
                
                print(f"微信API响应: {result}")
                
                if result.get('errcode') == 0:
                    print("✅ 微信消息发送成功！")
                    return True
                else:
                    print(f"❌ 微信消息发送失败: {result.get('errmsg')}")
                    # 如果是token错误，尝试重新获取token
                    if result.get('errcode') in [40001, 42001]:
                        print("🔄 token可能已过期，尝试重新获取...")
                        self.access_token = None
                        access_token = self.get_access_token()
                        if access_token:
                            url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                continue
                
                return False
                
            except Exception as e:
                print(f"❌ 发送微信消息异常 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        return False

def main():
    print("=" * 60)
    print(f"开始执行微信每日推送 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print("=" * 60)
    
    wechat = WeChatMessage()
    success = wechat.send_message()
    
    print("=" * 60)
    if success:
        print("✅ 每日推送成功！")
    else:
        print("❌ 推送失败")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    main()
