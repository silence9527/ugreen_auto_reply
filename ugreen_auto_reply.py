# ✅ 绿联社区自动回复签到脚本，v1.0
# ✅ By:Matata
# ✅ 新建环境变量名UGREEN_COOKIE，绿联社区首页https://club.ugnas.com/，登录后F12提取cookie填入即可

import requests, os, random, time, logging
from bs4 import BeautifulSoup
from datetime import datetime

# ✅ 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ugreen_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ✅ 获取 Cookie 和企业微信配置
UGREEN_COOKIE = os.getenv("UGREEN_COOKIE")
QYWX_AM = os.getenv("QYWX_AM")

if not UGREEN_COOKIE:
    logging.error("❌ 未检测到环境变量 UGREEN_COOKIE，脚本终止")
    exit()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": UGREEN_COOKIE
}

# ✅ 板块 URL（已更新）
FORUM_URLS = {
    "功能讨论": "https://club.ugnas.com/forum.php?mod=forumdisplay&fid=10",
    "玩法攻略": "https://club.ugnas.com/forum.php?mod=forumdisplay&fid=9",
    "用户互助": "https://club.ugnas.com/forum.php?mod=forumdisplay&fid=13"
}

# ✅ 多风格语料库
REPLY_STYLE = {
    "技术型": {
        "功能讨论": ["这个功能确实值得优化 👍", "建议加个远程端口配置选项", "我也遇到类似情况，建议官方看看", "这个问题我用 Docker 解决了 😎"],
        "玩法攻略": ["这个玩法太赞了 😄", "学习了新技巧，感谢分享", "我也试过这个方法，确实有效", "适合新手参考 👍"],
        "用户互助": ["我也遇到过类似问题 🤔", "建议检查网络设置", "可以试试重启设备", "这个方法值得一试"]
    },
    "热情型": {
        "功能讨论": ["太棒了这个建议！🔥", "支持楼主！", "功能细节讲得很清楚 👏", "希望官方采纳！"],
        "玩法攻略": ["感谢分享！我马上试试 😍", "这个教程太实用了", "赞一个！", "我来打卡学习了 💪"],
        "用户互助": ["大家都好热心！", "楼主的问题解决了吗？", "欢迎交流 👋", "希望你能顺利解决"]
    },
    "幽默型": {
        "功能讨论": ["这个功能让我头秃了 😂", "官方快来救命！", "我也踩过这个坑", "功能不够用，脑洞来凑 🤪"],
        "玩法攻略": ["这招太骚了！", "我抄作业来了 📝", "这波操作我给满分", "高手在民间啊 😆"],
        "用户互助": ["我来围观学习了 🧐", "这个问题我也翻车过", "大家都是技术人！", "互助区就是温暖 🧡"]
    }
}

# ✅ 获取帖子 ID 和标题
def get_thread_ids(forum_name, forum_url):
    try:
        res = requests.get(forum_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.select('a[href*="thread-"]')
        thread_ids = []
        for link in links:
            href = link.get('href')
            title = link.text.strip()
            if href and "thread-" in href:
                tid = href.split("thread-")[1].split("-")[0]
                thread_ids.append((forum_name, tid, title))
        return list(set(thread_ids))
    except Exception as e:
        logging.error(f"❌ 获取帖子列表失败：{e}")
        return []

# ✅ 获取 formhash
def get_formhash():
    try:
        url = "https://club.ugnas.com/forum.php?mod=post&action=newthread&fid=10"
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        formhash_input = soup.find('input', {'name': 'formhash'})
        if formhash_input:
            logging.info("✅ 成功提取 formhash")
            return formhash_input['value']
        else:
            logging.error("❌ 页面中未找到 formhash 字段")
            return None
    except Exception as e:
        logging.error(f"❌ 获取 formhash 异常：{e}")
        return None

# ✅ 发送回复
def post_reply(tid, message, formhash):
    global success_count, fail_count
    url = f"https://club.ugnas.com/forum.php?mod=post&action=reply&tid={tid}&replysubmit=yes&infloat=yes&handlekey=fastpost"
    data = {
        "message": message,
        "formhash": formhash,
        "posttime": int(time.time())
    }
    try:
        res = requests.post(url, headers=headers, data=data, timeout=10)
        if res.status_code == 200:
            success_count += 1
            logging.info(f"✅ 回复成功：帖子ID {tid} 内容：{message}")
        else:
            fail_count += 1
            logging.warning(f"⚠️ 回复失败：帖子ID {tid} 状态码 {res.status_code}")
    except Exception as e:
        fail_count += 1
        logging.error(f"❌ 回复异常：帖子ID {tid} 错误：{e}")

# ✅ 企业微信应用推送
def send_wechat_message(summary):
    if not QYWX_AM:
        logging.warning("⚠️ 未配置 QYWX_AM，跳过企业微信推送")
        return
    try:
        push_url = f"https://qyapi.pushplus.plus/send?token={QYWX_AM}&content={summary}&template=html"
        requests.get(push_url, timeout=5)
        logging.info("📢 企业微信推送成功")
    except Exception as e:
        logging.error(f"❌ 企业微信推送失败：{e}")

# ✅ 主流程
def main():
    global success_count, fail_count
    success_count = 0
    fail_count = 0
    style_usage = {}
    board_usage = {}
    keyword_hits = 0

    formhash = get_formhash()
    if not formhash:
        logging.error("❌ 获取 formhash 失败，终止执行")
        return

    all_threads = []
    for name, url in FORUM_URLS.items():
        tids = get_thread_ids(name, url)
        logging.info(f"📌 板块【{name}】获取到 {len(tids)} 个帖子")
        all_threads.extend(tids)

    if not all_threads:
        logging.error("❌ 未获取到任何帖子，终止执行")
        return

    styles = list(REPLY_STYLE.keys())
    style_today = styles[datetime.now().day % len(styles)]
    logging.info(f"🧑‍🎤 今日模拟风格：{style_today}")

    for board in REPLY_STYLE[style_today]:
        random.shuffle(REPLY_STYLE[style_today][board])

    keywords = ["远程", "端口", "Docker", "映射", "登录失败"]

    for i in range(20):
        forum_name, tid, title = random.choice(all_threads)
        if any(kw in title for kw in keywords):
            style_today = "技术型"
            keyword_hits += 1

        msg = random.choice(REPLY_STYLE[style_today][forum_name])
        style_usage[style_today] = style_usage.get(style_today, 0) + 1
        board_usage[forum_name] = board_usage.get(forum_name, 0) + 1

        post_reply(tid, msg, formhash)
        delay = random.randint(30, 600)
        logging.info(f"⏳ 等待 {delay} 秒后继续…")
        time.sleep(delay)

    summary = f"""绿联社区自动回复完成：
✅ 成功回复：{success_count}
❌ 失败回复：{fail_count}
🧑‍🎤 使用风格：{style_today}（{style_usage.get(style_today,0)} 次）
📌 板块分布：{board_usage}
🔍 关键词触发：{keyword_hits} 次
"""
    logging.info(summary)
    send_wechat_message(summary)

if __name__ == "__main__":
    logging.info("🚀 开始执行绿联云社区自动回复任务")
    main()
    logging.info("✅ 所有任务执行完毕")
