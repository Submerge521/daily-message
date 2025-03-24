"""
精准表名比对工具 v3.0 (精确模式)
更新时间：2025年3月14日 15:00
"""
import pandas as pd
from sqlalchemy import create_engine, inspect

# ============ 配置区 ============
DB_CONFIG = {
    "host": "10.10.10.215",
    "user": "etladmin",
    "password": "etladmin123",
    "database": "HG_SourceDB",
    "prefix": "tb_kjc_zw_",  # 必须严格匹配前缀大小写
    "port": 3306,
    "charset": "utf8mb4"
}

EXCEL_CONFIG = {
    "file_path": "3.xlsx",
    "sheet_name": 0,  # 第一个工作表
    "target_column": "源系统表英文名称(*)"
}
# ===============================

def strict_prefix_processing(raw_name: str) -> str:
    """严格处理前缀和格式"""
    processed = raw_name[len(DB_CONFIG["prefix"]):].strip()  # 仅去除前后空格
    return processed

def fetch_db_tables() -> dict:
    """获取数据库表名映射：原始表名 → 处理后表名"""
    try:
        engine = create_engine(
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            f"?charset={DB_CONFIG['charset']}"
        )
        inspector = inspect(engine)

        table_map = {}
        for raw_table in inspector.get_table_names(schema=DB_CONFIG["database"]):
            if raw_table.startswith(DB_CONFIG["prefix"]):
                clean_name = strict_prefix_processing(raw_table)
                if clean_name:  # 过滤空值
                    table_map[raw_table] = clean_name
        return table_map
    except Exception as e:
        raise RuntimeError(f"数据库连接失败：{str(e)}")

def read_excel_names() -> set:
    """读取Excel表名集合"""
    try:
        df = pd.read_excel(
            EXCEL_CONFIG["file_path"],
            sheet_name=EXCEL_CONFIG["sheet_name"],
            engine="openpyxl"
        )
        if EXCEL_CONFIG["target_column"] not in df.columns:
            raise ValueError(f"Excel中未找到列：'{EXCEL_CONFIG['target_column']}'")

        return {str(name).strip() for name in df[EXCEL_CONFIG["target_column"]].dropna()}
    except FileNotFoundError:
        raise RuntimeError(f"Excel文件未找到：{EXCEL_CONFIG['file_path']}")
    except Exception as e:
        raise RuntimeError(f"Excel读取失败：{str(e)}")

def main():
    try:
        # 数据获取
        db_map = fetch_db_tables()
        excel_set = read_excel_names()

        # 计算差异：数据库存在但Excel缺失的表
        db_processed = set(db_map.values())
        missing_tables = db_processed - excel_set

        # 结果输出
        if missing_tables:
            print("🚨 发现未匹配表名（数据库存在但Excel缺失）：")
            for raw_name, clean_name in db_map.items():
                if clean_name in missing_tables:
                    print(f" - 原始表名：{raw_name} → 处理后名称：{clean_name}")
        else:
            print("✅ 所有表名匹配成功")

    except Exception as e:
        print(f"❌ 程序执行失败：{str(e)}")
        exit(1)

if __name__ == "__main__":
    main()