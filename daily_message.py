import requests
import os
from datetime import datetime

# 从环境变量获取配置
SEND_KEY = os.getenv('SEND_KEY')
CITY = os.getenv('CITY', '广州')
BIRTHDAY = os.getenv('BIRTHDAY', '02-16')
GF_NAME = os.getenv('GF_NAME', '小睿')


def get_weather():
    """获取天气信息"""
    try:
        url = f"https://api.vvhan.com/api/weather?city={CITY}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('success'):
            info = data['info']
            return {
                'city': data['city'],
                'today': f"{info['type']} {info['low']}~{info['high']}°C",
                'tip': info.get('tip', '记得照顾好自己哦~')
            }
    except Exception as e:
        print(f"获取天气信息失败: {e}")
    return None


def get_horoscope():
    """获取星座运势（双鱼座）"""
    try:
        url = "https://api.vvhan.com/api/horoscope?type=pisces&time=today"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('success'):
            return {
                'lucky_color': data['data'].get('luckycolor', '墨绿色'),
                'match_sign': data['data'].get('shortcomment', '天秤座'),
                'fortune': data['data'].get('content', '今天会是美好的一天！')
            }
    except Exception as e:
        print(f"获取星座运势失败: {e}")
    return None


def calculate_days_until_birthday():
    """计算距离生日的天数"""
    try:
        today = datetime.now()
        year = today.year
        month, day = map(int, BIRTHDAY.split('-'))

        # 创建今年生日日期
        birthday_this_year = datetime(year, month, day)

        # 如果今年生日已过，计算明年的生日
        if today > birthday_this_year:
            birthday_next_year = datetime(year + 1, month, day)
            days_left = (birthday_next_year - today).days
        else:
            days_left = (birthday_this_year - today).days

        return days_left
    except Exception as e:
        print(f"计算生日天数失败: {e}")
        return None


def get_daily_sweet_words():
    """获取每日情话"""
    sweet_words = [
        "今天也是爱你的一天哦~ 💖",
        "你是我每天的阳光和温暖 ☀️",
        "想到你就觉得世界很美好 🌈",
        "每一天都因为有你而特别 ✨",
        "你是我最珍贵的宝贝 💎",
        "爱你是我做过最简单却最正确的事 ❤️",
        "今天也要开心哦，我的小太阳 🌞"
    ]
    import random
    return random.choice(sweet_words)


def generate_message():
    """生成每日消息"""
    # 获取各种信息
    weather = get_weather()
    horoscope = get_horoscope()
    days_until_birthday = calculate_days_until_birthday()
    sweet_words = get_daily_sweet_words()

    # 构建消息内容
    message = f"🌞 早安{GF_NAME}！\n\n"
    message += "📅 每日温馨提醒\n"
    message += f"日期: {datetime.now().strftime('%Y年%m月%d日')}\n"
    message += f"星期: {['一', '二', '三', '四', '五', '六', '日'][datetime.now().weekday()]}\n\n"

    if days_until_birthday is not None:
        message += f"🎂 距离生日还有: {days_until_birthday} 天\n\n"

    if weather:
        message += f"🌤️ 今日天气 ({weather['city']})\n"
        message += f"天气: {weather['today']}\n"
        message += f"小贴士: {weather['tip']}\n\n"

    message += "✨ 星座运势 (双鱼座)\n"
    if horoscope:
        message += f"幸运色: {horoscope['lucky_color']}\n"
        message += f"速配星座: {horoscope['match_sign']}\n"
        message += f"运势: {horoscope['fortune']}\n\n"
    else:
        message += "今天会是充满惊喜的一天！\n\n"

    message += f"💌 每日情话\n{sweet_words}\n\n"
    message += "——————————————\n"
    message += "💖 永远爱你的我\n"
    message += f"⏰ 发送时间: {datetime.now().strftime('%H:%M:%S')}"

    return message


def send_message():
    """发送消息到微信"""
    if not SEND_KEY:
        print("未设置SEND_KEY，无法发送消息")
        return False

    message = generate_message()
    print("生成的消息内容:\n")
    print(message)
    print("\n" + "=" * 50 + "\n")

    try:
        url = f"https://sctapi.ftqq.com/{SEND_KEY}.send"
        data = {
            "title": f"🌞 早安推送 - {datetime.now().strftime('%m月%d日')}",
            "desp": message
        }

        response = requests.post(url, data=data, timeout=10)
        result = response.json()

        if result.get('code') == 0:
            print("✅ 消息发送成功！")
            print(f"消息ID: {result.get('data', {}).get('pushid')}")
            return True
        else:
            print(f"❌ 消息发送失败: {result.get('message')}")
            return False

    except Exception as e:
        print(f"❌ 发送消息时出错: {e}")
        return False


if __name__ == "__main__":
    print("开始生成每日消息...\n")
    send_message()
