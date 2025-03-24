import pandas as pd
from urllib.parse import quote
from sqlalchemy import create_engine

# 数据库连接配置
DB_CONFIG = {
    "host": "10.10.10.243",
    "port": 3306,
    "user": "root",
    "password": quote("root123!@#"),
    "database": "intelligent_report",
}
# 忽略的列
IGNORED_EXCEL_COLUMNS = [
    "主键数据唯一性标识（32位全局唯一编码字符串（大写字母+数字组合））-zjsjwyxbs",
    "学校代码（学校（机构）标识码，10位数字码）-xxdm"
]
IGNORED_MYSQL_COLUMNS = ["id", "XXDM"]


def read_excel_data(file_path, mysql_columns):
    """
    读取 Excel 数据，忽略指定列，并统一字段顺序。
    """
    # 读取 Excel 文件
    df = pd.read_excel(file_path)
    # 创建列名映射规则
    column_mapping = {col: col.split("-")[-1].strip().upper() for col in df.columns}
    # 重命名列
    df.rename(columns=column_mapping, inplace=True)
    # 移除 Excel 中忽略的列
    for ignored_column in IGNORED_EXCEL_COLUMNS:
        mapped_column = ignored_column.split("-")[-1].strip().upper()
        if mapped_column in df.columns:
            df.drop(columns=[mapped_column], inplace=True)
    # 按照 MySQL 列的顺序重新排列，但移除 MySQL 忽略的列
    mysql_columns = [col for col in mysql_columns if col not in IGNORED_MYSQL_COLUMNS]
    df = df[[col for col in mysql_columns if col in df.columns]]
    return df


def read_db_data(table_name, db_config):
    """
    从数据库中读取数据，忽略指定列。
    """
    connection_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    engine = create_engine(connection_url)
    with engine.connect() as connection:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, connection)
        # 移除 MySQL 中忽略的列
        for col in IGNORED_MYSQL_COLUMNS:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)
        return df


def compare_data_row_by_row(excel_data, db_data):
    """
    按行逐列比较数据，仅对比值是否相等，忽略数据类型。
    """
    diff_report = []

    # 确保两边行数一致
    if len(excel_data) != len(db_data):
        raise ValueError("Excel 和 MySQL 数据行数不一致，无法逐行比较！")

    # 遍历每一行进行比较
    for index in range(len(excel_data)):
        excel_row = excel_data.iloc[index]
        db_row = db_data.iloc[index]

        for column in excel_data.columns:
            if column in db_data.columns:
                # 获取值并统一为字符串形式
                excel_value = excel_row[column]
                db_value = db_row[column]

                # 仅比较值是否相等，忽略类型
                if pd.isna(excel_value) and pd.isna(db_value):
                    # 如果两边都为空，则视为相等
                    continue
                elif str(excel_value) != str(db_value):
                    # 值不相等时记录差异
                    diff_report.append({
                        "行号": index + 1,  # 行号从 1 开始
                        "列名": column,
                        "Excel 值": excel_value,
                        "数据库值": db_value,
                    })

    return diff_report


def main():
    """
    手动运行的主程序。
    """
    excel_path = input("请输入完整Excel表的路径")
    table_name = input("请输入英文表名")

    try:
        print(f"正在验证 {excel_path} 和数据库表 {table_name} 的数据...")

        # 从数据库读取列名
        connection_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(connection_url)
        with engine.connect() as connection:
            mysql_columns = pd.read_sql(f"DESCRIBE {table_name}", connection)["Field"].tolist()

        # 读取 Excel 数据
        excel_data = read_excel_data(excel_path, mysql_columns)

        # 读取数据库数据
        db_data = read_db_data(table_name, DB_CONFIG)

        # 比较数据逐行差异
        diff_report = compare_data_row_by_row(excel_data, db_data)

        if not diff_report:
            print(f"{excel_path} 和 {table_name} 数据完全一致！")
        else:
            print(f"{excel_path} 和 {table_name} 存在逐行差异：")
            for diff in diff_report:
                print(f"行号: {diff['行号']}, 列名: {diff['列名']}, Excel 值: {diff['Excel 值']}, 数据库值: {diff['数据库值']}")
            # 保存差异报告到 CSV
            pd.DataFrame(diff_report).to_csv("row_by_row_differences.csv", index=False, encoding="utf-8-sig")
            print("差异报告已保存为 'row_by_row_differences.csv'")
    except FileNotFoundError:
        print(f"文件 {excel_path} 不存在，请检查路径！")
    except Exception as e:
        print(f"验证过程中发生错误：{e}")


if __name__ == "__main__":
    while True:
        main()
