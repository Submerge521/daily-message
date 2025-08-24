import requests
import os
import json
from datetime import datetime

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
        # 如果token还有效，直接返回
        if self.access_token and datetime.now().timestamp() < self.token_expire_time:
            return self.access_token
            
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if 'access_token' in data:
                self.access_token = data['access_token']
                self.token_expire_time = datetime.now().timestamp() + data['expires_in'] - 300  # 提前5分钟过期
                print("✅ 获取access_token成功")
                return self.access_token
            else:
                print(f"❌ 获取access_token失败: {data}")
                return None
        except Exception as e:
            print(f"❌ 获取access_token异常: {e}")
            return None
    
    def get_weather(self):
        """获取天气信息"""
        try:
            url = f"https://api.vvhan.com/api/weather?city={CITY}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('success'):
                info = data['info']
                return f"{info['type']} {info['low']}~{info['high']}°C"
        except Exception as e:
            print(f"获取天气信息失败: {e}")
        return "暂无天气信息"
    
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
                
            return f"{days_left}天"
        except Exception as e:
            print(f"计算生日天数失败: {e}")
        return "未知"
    
    def get_horoscope(self):
        """获取星座运势"""
        try:
            url = "https://api.vvhan.com/api/horoscope?type=pisces&time=today"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('success'):
                content = data['data'].get('content', '')
                # 截取前50个字
                return content[:50] + "..." if len(content) > 50 else content
        except Exception as e:
            print(f"获取星座运势失败: {e}")
        return "今天会是美好的一天"
    
    def get_sweet_words(self):
        """获取每日情话"""
        sweet_words = [
            "今天也是爱你的一天哦~",
            "你是我每天的阳光和温暖",
            "想到你就觉得世界很美好",
            "每一天都因为有你而特别",
            "你是我最珍贵的宝贝",
            "爱你是我做过最简单却最正确的事",
            "今天也要开心哦，我的小太阳"
        ]
        import random
        return random.choice(sweet_words)
    
    def send_message(self):
        """发送微信模板消息"""
        if not all([APPID, APPSECRET, TEMPLATE_ID, USER_ID]):
            print("❌ 微信配置信息不完整")
            print(f"APPID: {APPID}")
            print(f"APPSECRET: {'已设置' if APPSECRET else '未设置'}")
            print(f"TEMPLATE_ID: {TEMPLATE_ID}")
            print(f"USER_ID: {USER_ID}")
            return False
        
        access_token = self.get_access_token()
        if not access_token:
            return False
        
        # 准备消息数据
        weather = self.get_weather()
        birthday_countdown = self.calculate_days_until_birthday()
        horoscope = self.get_horoscope()
        sweet_words = self.get_sweet_words()
        
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        current_weekday = weekdays[datetime.now().weekday()]
        
        template_data = {
            "touser": USER_ID,
            "template_id": TEMPLATE_ID,
            "url": "https://github.com",  # 可点击跳转的链接
            "data": {
                "first": {
                    "value": f"🌞 早安{GF_NAME}！",
                    "color": "#FF6699"
                },
                "date": {
                    "value": datetime.now().strftime('%Y年%m月%d日'),
                    "color": "#666666"
                },
                "week": {
                    "value": f"星期{current_weekday}",
                    "color": "#666666"
                },
                "birthday": {
                    "value": birthday_countdown,
                    "color": "#FF9900"
                },
                "weather": {
                    "value": weather,
                    "color": "#3399FF"
                },
                "horoscope": {
                    "value": horoscope,
                    "color": "#9933CC"
                },
                "sweetWords": {
                    "value": sweet_words,
                    "color": "#FF6666"
                },
                "remark": {
                    "value": "💖 永远爱你的我",
                    "color": "#999999"
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
    print("开始执行微信测试号推送")
    print("=" * 60)
    
    # 检查必要配置
    required_envs = ['WECHAT_APPID', 'WECHAT_APPSECRET', 'WECHAT_TEMPLATE_ID', 'WECHAT_USER_ID']
    missing_envs = [env for env in required_envs if not os.getenv(env)]
    
    if missing_envs:
        print(f"❌ 缺少环境变量: {', '.join(missing_envs)}")
        print("请在GitHub Secrets中设置这些变量")
        return False
    
    wechat = WeChatMessage()
    success = wechat.send_message()
    
    print("=" * 60)
    if success:
        print("✅ 推送成功！")
    else:
        print("❌ 推送失败")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    main()
