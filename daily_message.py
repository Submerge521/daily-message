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
CITY = os.getenv('CITY', '广州')
BIRTHDAY = os.getenv('BIRTHDAY', '02-16')
GF_NAME = os.getenv('GF_NAME', '小睿')

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
        """获取天气信息 - 使用多个API备用"""
        apis = [
            self._get_weather_api1,
            self._get_weather_api2,
            self._get_weather_api3
        ]
        
        # 随机选择一个API尝试
        random.shuffle(apis)
        for api in apis:
            try:
                result = api()
                if result:
                    return result
            except:
                continue
        
        # 所有API都失败时使用本地数据
        weather_options = [
            "🌞 晴 26°C~35°C | 阳光明媚，适合出门散步",
            "⛅ 多云 24°C~32°C | 云朵飘飘，心情也轻松",
            "🌧️ 小雨 22°C~28°C | 细雨绵绵，记得带伞哦",
            "🌤️ 晴转多云 25°C~33°C | 天气多变，注意增减衣物",
            "❄️ 凉爽 20°C~26°C | 秋风送爽，很舒服的天气"
        ]
        return random.choice(weather_options)
    
    def _get_weather_api1(self):
        """天气API1"""
        try:
            url = f"http://wttr.in/{CITY}?format=%C+%t"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                weather = response.text.strip()
                return f"{weather} | 美好的一天从好天气开始~"
        except:
            return None
    
    def _get_weather_api2(self):
        """天气API2"""
        try:
            url = f"https://api.vvhan.com/api/weather?city={CITY}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                info = data['info']
                return f"{info['type']} {info['low']}~{info['high']}°C | 记得{self._get_weather_tip(info['type'])}"
        except:
            return None
    
    def _get_weather_api3(self):
        """天气API3"""
        try:
            # 使用和风天气的免费API（需要注册）
            # 如果没有注册，可以注释掉这个API
            return None
        except:
            return None
    
    def _get_weather_tip(self, weather_type):
        """天气提示"""
        tips = {
            "晴": "涂防晒，小仙女要白白嫩嫩的",
            "多云": "云朵像棉花糖，心情也会甜甜的",
            "阴": "阴天也要保持微笑哦",
            "雨": "记得带伞，不想你淋雨",
            "雪": "下雪啦！要穿暖暖的"
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
            
            if days_left == 0:
                return "🎉 今天是生日！生日快乐我的宝贝！"
            elif days_left == 1:
                return "🌟 明天生日！已经准备好惊喜啦~"
            elif days_left < 7:
                return f"🎂 还有{days_left}天！超级期待！"
            elif days_left < 30:
                return f"💝 还有{days_left}天，每天都在想你"
            else:
                return f"📅 还有{days_left}天，但爱你的心从不停止"
                
        except:
            return "🎁 生日总是最特别的日子"
    
    def get_horoscope(self):
        """获取星座运势 - 多个API备用"""
        apis = [
            self._get_horoscope_api1,
            self._get_horoscope_api2,
            self._get_horoscope_api3
        ]
        
        random.shuffle(apis)
        for api in apis:
            try:
                result = api()
                if result:
                    return result
            except:
                continue
        
        # 备用本地运势
        horoscopes = [
            "🌟 今天会有意想不到的惊喜哦",
            "💖 爱情运势满分，适合表达心意",
            "🌈 整体运势很棒，做什么都很顺利",
            "🎯 是实现目标的好时机，加油",
            "✨ 幸运女神眷顾着你呢"
        ]
        return random.choice(horoscopes)
    
    def _get_horoscope_api1(self):
        """星座API1"""
        try:
            url = "https://api.azhubaby.com/constellation/pisces/"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                return data.get('content', '')[:50] + "..."
        except:
            return None
    
    def _get_horoscope_api2(self):
        """星座API2"""
        try:
            url = "https://api.vvhan.com/api/horoscope?type=pisces&time=today"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                return data['data'].get('content', '')[:50] + "..."
        except:
            return None
    
    def _get_horoscope_api3(self):
        """星座API3"""
        try:
            url = "https://api.btstu.cn/yan/api.php?charset=utf-8"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()[:40] + "..."
        except:
            return None
    
    def get_daily_quote(self):
        """获取每日一句 - 多个API随机调用"""
        apis = [
            self._get_quote_api1,
            self._get_quote_api2,
            self._get_quote_api3,
            self._get_quote_api4
        ]
        
        random.shuffle(apis)
        for api in apis:
            try:
                result = api()
                if result:
                    return result
            except:
                continue
        
        # 备用本地名言
        quotes = [
            "生活不是等待风暴过去，而是学会在雨中跳舞。",
            "每一天都是新的开始，珍惜当下。",
            "微笑是最好的化妆品，快乐是最好的保养品。",
            "心中有爱，眼里有光，生活就有希望。",
            "简单的快乐最持久，平凡的日子最珍贵。"
        ]
        return random.choice(quotes)
    
    def _get_quote_api1(self):
        """每日一句API1"""
        try:
            url = "https://api.xygeng.cn/one"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('code') == 200:
                return data.get('data', {}).get('content', '')
        except:
            return None
    
    def _get_quote_api2(self):
        """每日一句API2"""
        try:
            url = "https://v1.hitokoto.cn/?c=d&c=i&c=k"
            response = requests.get(url, timeout=5)
            data = response.json()
            return data.get('hitokoto', '') + " ——" + data.get('from', '')
        except:
            return None
    
    def _get_quote_api3(self):
        """每日一句API3"""
        try:
            url = "https://api.btstu.cn/yan/api.php?charset=utf-8"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            return None
    
    def _get_quote_api4(self):
        """每日一句API4"""
        try:
            url = "https://api.mcloc.cn/yan/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            return None
    
    def get_daily_tip(self):
        """获取温馨提醒 - 多个API随机调用"""
        apis = [
            self._get_tip_api1,
            self._get_tip_api2,
            self._get_tip_api3
        ]
        
        random.shuffle(apis)
        for api in apis:
            try:
                result = api()
                if result:
                    return result
            except:
                continue
        
        # 备用本地提醒
        tips = [
            "记得喝够8杯水，保持水润润的",
            "今天也要好好吃饭，不要饿着",
            "保持微笑，你的笑容最美",
            "适当休息，别让自己太累",
            "出门前检查物品，别忘带东西"
        ]
        return random.choice(tips)
    
    def _get_tip_api1(self):
        """提醒API1"""
        try:
            url = "https://api.btstu.cn/tips/api.php?charset=utf-8"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            return None
    
    def _get_tip_api2(self):
        """提醒API2"""
        try:
            url = "https://api.mcloc.cn/tips/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            return None
    
    def _get_tip_api3(self):
        """提醒API3"""
        # 可以添加其他提醒API
        return None
    
    def get_sweet_words(self):
        """获取情话 - 多个API随机调用"""
        apis = [
            self._get_sweet_api1,
            self._get_sweet_api2,
            self._get_sweet_api3
        ]
        
        random.shuffle(apis)
        for api in apis:
            try:
                result = api()
                if result:
                    return result
            except:
                continue
        
        # 备用本地情话
        sweet_words = [
            "🐰 今天也是想扑进你怀里的一天",
            "🌟 你是我生命中最亮的星星",
            "💕 爱你是我做过最正确的决定",
            "🍬 和你在一起的每一天都甜甜蜜蜜",
            "🌻 你是我的小太阳，温暖我的心"
        ]
        return random.choice(sweet_words)
    
    def _get_sweet_api1(self):
        """情话API1"""
        try:
            url = "https://api.btstu.cn/saylove/api.php?charset=utf-8"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            return None
    
    def _get_sweet_api2(self):
        """情话API2"""
        try:
            url = "https://api.mcloc.cn/love/"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            return None
    
    def _get_sweet_api3(self):
        """情话API3"""
        try:
            url = "https://api.vvhan.com/api/love"
            response = requests.get(url, timeout=5)
            data = response.json()
            if data.get('success'):
                return data.get('ishan', '')
        except:
            return None
    
    def get_description(self):
        """获取顶部描述文字"""
        descriptions = [
            f"🌞 早安{GF_NAME}！新的一天开始啦~",
            f"🌸 亲爱的{GF_NAME}，今天也要开心哦",
            f"🐻 {GF_NAME}宝贝，醒来收到我的爱了吗",
            f"🌟 早上好我的小仙女{GF_NAME}",
            f"💖 {GF_NAME}，今天的推送准时送达啦",
            f"🎀 公主殿下{GF_NAME}，请查收今日份温柔",
            f"🍯 甜心{GF_NAME}，一天的美好从此刻开始",
            f"🚀 {GF_NAME}，准备开启今天的冒险吧"
        ]
        return random.choice(descriptions)
    
    def get_remark(self):
        """获取底部备注"""
        remarks = [
            "💖 永远爱你的我 | 🌈 每一天都因你而美好",
            "🤗 想你的每一刻 | 🎯 今天也要加油哦",
            "🐾 你的专属温暖 | 🌟 期待与你的每一天",
            "🍀 幸运常相伴 | 💕 爱意永不止息",
            "🎨 生活因你多彩 | ☀️ 心情因你晴朗"
        ]
        return random.choice(remarks)
    
    def send_message(self):
        """发送微信模板消息"""
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
        daily_quote = self.get_daily_quote()
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
                "dailyQuote": {
                    "value": daily_quote,
                    "color": "#5D7092"
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
