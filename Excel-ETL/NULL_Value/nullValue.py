import argparse
import sys
from typing import List

# 驱动配置（仅加载必要模块）
try:
    import mysql.connector
    import cx_Oracle
except ImportError as e:
    print(f"模块缺失: {e}\n安装命令: pip install mysql-connector-python cx_Oracle")
    sys.exit(1)


def secure_get_tables(db_type: str, conn) -> List[str]:
    """安全获取表清单（适配低权限场景）"""
    cursor = conn.cursor()
    try:
        if db_type == "mysql":
            # 使用SHOW TABLES规避information_schema权限问题
            cursor.execute("SHOW  TABLES")
            return [t[0] for t in cursor.fetchall()]
        elif db_type == "oracle":
            # 使用用户级视图（需至少SELECT_CATALOG_ROLE权限）
            cursor.execute("SELECT  table_name FROM user_tables")
            return [t[0] for t in cursor.fetchall()]
    except Exception as e:
        if "ORA-00942" in str(e):  # Oracle表/视图不存在错误
            print("权限不足：请确认拥有SELECT_CATALOG_ROLE角色")
        elif "1142" in str(e):  # MySQL SHOW命令错误
            print("权限不足：需要SHOW TABLES权限")
        sys.exit(1)
    finally:
        cursor.close()


def minimal_permission_check(db_type: str, conn):
    """最低权限验证"""
    test_table = "permission_check_temp"
    cursor = conn.cursor()
    try:
        if db_type == "mysql":
            cursor.execute(f"SELECT  1 FROM {test_table} LIMIT 1")
        elif db_type == "oracle":
            cursor.execute(f"SELECT  1 FROM {test_table} WHERE ROWNUM < 2")
    except Exception as e:
        if "ORA-00942" in str(e) or "1142" in str(e):
            print(f"权限验证失败：无法读取测试表 {test_table}")
            sys.exit(1)
    finally:
        cursor.close()


if __name__ == "__main__":
    # [...] 保留原有参数解析和连接逻辑

    # 新增权限预检
    minimal_permission_check(args.type, conn)

    # 获取表清单（使用安全方法）
    tables = secure_get_tables(args.type, conn)

    # [...] 后续检测逻辑保持不变
