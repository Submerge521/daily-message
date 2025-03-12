import subprocess
import datetime
import configparser
import time

import requests
import json
import os


def send_feishu_notification(message, webhook_url):
    """
    发送飞书通知
    """
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        print(f"发送飞书通知失败: {response.text}")


def backup_database(db_name, user, password, host, port, webhook_url, results):
    """
    备份数据库
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "/opt/backup"  # 指定备份目录
    os.makedirs(backup_dir, exist_ok=True)  # 确保目录存在
    backup_file = os.path.join(backup_dir, f"{db_name}_backup_{timestamp}.sql")

    # 整合消息
    results[db_name] = {"backup_file": backup_file}
    print(f"备份文件路径: {backup_file}")

    command = ['mysqldump', '-h', host, '-P', str(port), '-u', user, '-p' + password, db_name,
               '--result-file=' + backup_file]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            error_message = f"备份数据库 {db_name} 时发生错误:\n{result.stderr}"
            print(error_message)
            results[db_name]["error"] = error_message
            send_feishu_notification(error_message, webhook_url)
            return False

        success_message = f"数据库 {db_name} 备份成功，备份文件: {backup_file}"
        print(success_message)
        results[db_name]["success"] = success_message

        if os.path.exists(backup_file):
            results[db_name]["file_created"] = f"备份文件已创建: {backup_file}"
        else:
            results[db_name]["file_created"] = "备份文件未创建。"

        # 传输备份文件到远程服务器
        remote_backup_dir = "/opt/backup"  # 目标服务器的备份目录
        scp_command = ['scp', backup_file, f"{server_user}@{remote_server}:{remote_backup_dir}"]
        scp_result = subprocess.run(scp_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if scp_result.returncode != 0:
            error_message = f"SCP传输 {db_name} 备份文件时发生错误:\n{scp_result.stderr}"
            print(error_message)
            results[db_name]["scp_error"] = error_message
            # send_feishu_notification(error_message, webhook_url)
        else:
            success_message = f"数据库 {db_name} 备份文件已成功传输至远程服务器。"
            print(success_message)
            results[db_name]["scp_success"] = success_message
            # send_feishu_notification(success_message, webhook_url)

        # 删除旧的备份文件，只保留最新的一个
        cleanup_old_backups(backup_dir, db_name)
        # send_feishu_notification(success_message, webhook_url)
        return True

    except Exception as e:
        error_message = f"发生错误: {e}"
        print(error_message)
        results[db_name]["error"] = error_message
        # send_feishu_notification(error_message, webhook_url)
        return False


def cleanup_old_backups(backup_dir, db_name):
    """
    删除旧的备份文件，只保留最新的一个
    """
    # 获取当前时间
    now = time.time()
    latest_backup = None  # 用于存储最新备份文件的路径

    # 遍历备份目录
    for file in os.listdir(backup_dir):
        if file.startswith(f"{db_name}_backup_"):
            file_path = os.path.join(backup_dir, file)
            # 检查文件的最后修改时间
            if os.path.isfile(file_path):
                # 更新最新备份文件
                if latest_backup is None or os.path.getmtime(file_path) > os.path.getmtime(latest_backup):
                    latest_backup = file_path

    # 删除旧的备份文件，只保留最新的一个
    for file in os.listdir(backup_dir):
        if file.startswith(f"{db_name}_backup_"):
            file_path = os.path.join(backup_dir, file)
            if file_path != latest_backup:  # 只删除不是最新的备份文件
                os.remove(file_path)
                print(f"删除旧的备份文件: {file}")
                send_feishu_notification(f"删除旧的备份文件: {file}", webhook_url)


def check_mysql_database(db_name, user, password, host, port, webhook_url, results):
    """
    检查数据库
    """
    command = ['mysqlcheck', '-h', host, '-P', str(port), '-u', user, '-p' + password, '--databases', db_name,
               '--auto-repair']

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            error_message = f"执行 mysqlcheck 时发生错误:\n{result.stderr}"
            print(error_message)
            results[db_name]["check_error"] = error_message
            # send_feishu_notification(error_message, webhook_url)
            return

        output_lines = result.stdout.splitlines()
        not_ok_tables = []

        for line in output_lines:
            if "OK" not in line and "repair" in line:
                not_ok_tables.append(line)

        if not_ok_tables:
            warning_message = "以下表存在问题：\n" + "\n".join(not_ok_tables)
            print(warning_message)
            results[db_name]["check_warning"] = warning_message
            # send_feishu_notification(warning_message, webhook_url)
        else:
            success_message = f"数据库 {db_name} 所有表检查正常。"
            print(success_message)
            results[db_name]["check_success"] = success_message
            # send_feishu_notification(success_message, webhook_url)

    except Exception as e:
        error_message = f"发生错误: {e}"
        print(error_message)
        results[db_name]["check_error"] = error_message
        # send_feishu_notification(error_message, webhook_url)


def read_db_config(filename):
    """
    读取数据库配置
    """
    config = configparser.ConfigParser()
    config.read(filename)
    return config


# 使用示例
if __name__ == "__main__":
    config = read_db_config('./config.ini')

    # 读取数据库的公共配置
    host = config['database']['host']
    port = config.getint('database', 'port')
    user = config['database']['user']
    password = config['database']['password']
    webhook_url = config['database'].get('webhook_url', 'your_feishu_webhook_url')  # 添加 webhook_url
    remote_server = config['database']['remote_server']  # 远程服务器地址
    server_user = config['database']['server_user']
    # 初始化结果字典
    results = {}

    # 读取第一个数据库的名称
    db1_name = config['databases']['db1']

    # 备份第一个数据库
    if backup_database(db1_name, user, password, host, port, webhook_url, results):
        check_mysql_database(db1_name, user, password, host, port, webhook_url, results)

    # 读取第二个数据库的名称
    db2_name = config['databases']['db2']

    # 备份第二个数据库
    if backup_database(db2_name, user, password, host, port, webhook_url, results):
        check_mysql_database(db2_name, user, password, host, port, webhook_url, results)

        # 将结果字典转换为字符串
    results_message = json.dumps(results, ensure_ascii=False, indent=4)

    # 推送最终结果到飞书
    send_feishu_notification(f"最终结果:\n{results_message}", webhook_url)
