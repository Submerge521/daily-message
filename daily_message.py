import requests
import os
import json
from datetime import datetime
import random

# 从环境变量获取配置
APPID = os.getenv('WECHAT_APPID')
APPSECRET = os.getenv('WECHAT_APPSECRET')
TEMPLATE_ID = os.getenv('WECHAT_TEMPLATE_ID')
USER_ID = os.getenv('WECHAT_USER_ID')
CITY = os.getenv('CITY', '苏州')
BIRTHDAY = os.getenv('BIRTHDAY', '02-23')
GF_NAME = os.getenv('GF_NAME', '宝贝')

class WeChatMessage:
    def __init__(self):
        self.access_token = None
        self.token_expire_time = 0
        
    def get_access_token(self):
        """获取微信access_token"""
        if self.access_token and datetime.now().timestamp() < self.token_expire_time:
            return self.access_token
            
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if 'access_token' in data:
                self.access_token = data['access_token']
                self.token_expire_time = datetime.now().timestamp() + data['expires_in'] - 300
                print("✅ 获取access_token成功")
                return self.access_token
            else:
                print(f"❌ 获取access_token失败: {data}")
                return None
        except Exception as e:
            print(f"❌ 获取access_token异常: {e}")
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
                temp_range = f"{info['low']}~{info['high']}°C"
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
        
        if month in [12, 1, 2]:  # 冬季
            weathers = ["❄️ 晴 -2°C~8°C | 冬天来了，记得穿暖暖", "🌨️ 雪 -5°C~2°C | 下雪啦，小心路滑"]
        elif month in [3, 4, 5]:  # 春季
            weathers = ["🌸 晴 15°C~25°C | 春暖花开，适合散步", "🌧️ 小雨 12°C~18°C | 春雨绵绵，带把伞吧"]
        elif month in [6, 7, 8]:  # 夏季
            weathers = ["🌞 晴 28°C~36°C | 热浪来袭，注意防暑", "⛈️ 雷阵雨 26°C~32°C | 可能有雨，带伞出门"]
        else:  # 秋季
            weathers = ["🍂 晴 18°C~26°C | 秋高气爽，很舒服呢", "🌫️ 多云 16°C~22°C | 云淡风轻，适合郊游"]
        
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
            today = datetime.now()
            year = today.year
            month, day = map(int, BIRTHDAY.split('-'))
            
            birthday_this_year = datetime(year, month, day)
            
            if today > birthday_this_year:
                birthday_next_year = datetime(year + 1, month, day)
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
    
    def get_horoscope(self):
        """获取星座运势 - 确保一定有返回"""
        print("正在获取星座运势...")
        
        # 尝试多个星座API
        horoscope_apis = [
            self._try_azhubaby_horoscope,
            self._try_vvhan_horoscope,
            self._try_btstu_horoscope
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
    
    def _try_azhubaby_horoscope(self):
        """尝试azhubaby星座API"""
        try:
            url = "https://api.azhubaby.com/constellation/pisces/"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                content = data.get('content', '')
                if content:
                    return f"✨ {content[:45]}..."
        except:
            return None
    
    def _try_vvhan_horoscope(self):
        """尝试vvhan星座API"""
        try:
            url = "https://api.vvhan.com/api/horoscope?type=pisces&time=today"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                content = data['data'].get('content', '')
                if content:
                    return f"✨ {content[:45]}..."
        except:
            return None
    
    def _try_btstu_horoscope(self):
        """尝试btstu星座API"""
        try:
            url = "https://api.btstu.cn/yan/api.php?charset=utf-8"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return f"✨ {response.text.strip()[:40]}..."
        except:
            return None
    
    def _get_local_horoscope(self):
        """获取本地星座运势"""
        horoscopes = [
            "🌟 双鱼座今天运势很棒！感情方面会有小惊喜，保持开放的心态~",
            "💫 今天适合创意工作，你的直觉很准，相信自己的感觉吧！",
            "🌈 整体运势不错，可能会遇到意想不到的好事，保持微笑~",
            "🎯 是制定计划的好时机，你的梦想正在一步步实现呢",
            "❤️ 爱情运势佳，适合表达心意，对方会被你的真诚打动"
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
            "记得给家人打个电话，他们很想你",
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
            "🐰 今天也是想扑进你怀里的一天~",
            "🌟 你是我生命中最亮的星星",
            "💕 爱你是我做过最正确的决定",
            "🍬 和你在一起的每一天都甜甜蜜蜜",
            "🌻 你是我的小太阳，温暖我的心",
            "🎯 我的目标就是让你每天都开心",
            "🌈 遇见你是我最大的幸运",
            "🎁 你就是我最好的礼物"
        ]
        return f"💌 {random.choice(sweet_words)}"
    
    def get_description(self):
        """获取顶部描述"""
        descriptions = [
            f"🌞 早安{GF_NAME}！新的一天开始啦~",
            f"🌸 亲爱的{GF_NAME}，今天也要开心哦",
            f"🐻 {GF_NAME}宝贝，醒来收到我的爱了吗",
            f"🌟 早上好我的小仙女{GF_NAME}",
            f"💖 {GF_NAME}，今天的推送准时送达啦"
        ]
        return random.choice(descriptions)
    
    def get_remark(self):
        """获取底部备注"""
        remarks = [
            "💖 永远爱你的我 | 🌈 每一天都因你而美好",
            "🤗 想你的每一刻 | 🎯 今天也要加油哦",
            "🐾 你的专属温暖 | 🌟 期待与你的每一天"
        ]
        return random.choice(remarks)
    
    def send_message(self):
        """发送微信模板消息"""
        print("开始准备消息内容...")
        
        if not all([APPID, APPSECRET, TEMPLATE_ID, USER_ID]):
            print("❌ 微信配置信息不完整")
            return False
        
        access_token = self.get_access_token()
        if not access_token:
            return False
        
        # 准备消息数据
        description = self.get_description()
        weather = self.get_weather()
        birthday_countdown = self.calculate_days_until_birthday()
        horoscope = self.get_horoscope()
        sweet_words = self.get_sweet_words()
        daily_tip = self.get_daily_tip()
        remark = self.get_remark()
        
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        current_weekday = weekdays[datetime.now().weekday()]
        
        template_data = {
            "touser": USER_ID,
            "template_id": TEMPLATE_ID,
            "url": "https://github.com",
            "data": {
                "description": {
                    "value": description,
                    "color": "#FF6B9D"
                },
                "date": {
                    "value": datetime.now().strftime('%Y年%m月%d日'),
                    "color": "#5B8FF9"
                },
                "week": {
                    "value": f"星期{current_weekday}",
                    "color": "#5B8FF9"
                },
                "birthday": {
                    "value": birthday_countdown,
                    "color": "#FF9D4D"
                },
                "weather": {
                    "value": weather,
                    "color": "#30BF78"
                },
                "horoscope": {
                    "value": horoscope,
                    "color": "#9A5FE8"
                },
                "sweetWords": {
                    "value": sweet_words,
                    "color": "#FF6B6B"
                },
                "dailyTip": {
                    "value": daily_tip,
                    "color": "#FFC53D"
                },
                "remark": {
                    "value": remark,
                    "color": "#FF85C0"
                }
            }
        }
        
        print("消息内容准备完成，开始发送...")
        
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
        
        try:
            response = requests.post(url, json=template_data, timeout=10)
            result = response.json()
            
            print(f"微信API响应: {result}")
            
            if result.get('errcode') == 0:
                print("✅ 微信消息发送成功！")
                return True
            else:
                print(f"❌ 微信消息发送失败: {result.get('errmsg')}")
                return False
                
        except Exception as e:
            print(f"❌ 发送微信消息异常: {e}")
            return False

def main():
    print("=" * 60)
    print("开始执行微信每日推送")
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
