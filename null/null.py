import argparse
import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import URL
from prettytable import PrettyTable
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class NullAnalyzer:
    def __init__(self, db_type, table_name):
        self.db_type = db_type.lower()
        self.table_name = table_name
        self.engine = self._connect_db()
        self.inspector = inspect(self.engine)

    def _connect_db(self):
        """动态构建数据库连接"""
        default_ports = {'mysql': 3306, 'postgresql': 5432, 'oracle': 1521}
        port = int(os.getenv('DB_PORT', default_ports.get(self.db_type, 3306)))
        return create_engine(URL(
            drivername=self._get_driver_name(),
            username=os.getenv('DB_USER', 'etladmin'),
            password=os.getenv('DB_PASSWORD', 'etladmin123'),
            host=os.getenv('DB_HOST', '10.10.10.215'),
            database=os.getenv('DB_NAME', 'HG_SourceDB'),
            port=port,
            query={'charset': 'utf8mb4'}
        ))

    def _get_driver_name(self):
        """选择数据库驱动"""
        drivers = {
            'mysql': 'mysql+pymysql',
            'oracle': 'oracle+cx_oracle',
            'postgresql': 'postgresql+psycopg2'
        }
        return drivers.get(self.db_type, 'mysql+pymysql')

    def _generate_null_sql(self, column):
        """生成空值统计SQL表达式"""
        return ("SUM(CASE WHEN {0} IS NULL THEN 1 ELSE 0 END)" if self.db_type == 'oracle'
                else "SUM({0} IS NULL)").format(column)

    def _get_null_description(self, null_rate):
        """空值率语义化描述"""
        if 95 <= null_rate <= 100.0:
            return "无数据"
        elif 85 <= null_rate < 95:
            return "基本为空"
        elif 45 <= null_rate <= 55:
            return "一半为空"
        else:
            return "√"

    def analyze(self):
        """执行空值分析并输出结果"""
        try:
            # 获取可分析字段列表
            columns = [
                col['name'] for col in self.inspector.get_columns(self.table_name)
                if not isinstance(col['type'].python_type, (bytes, bytearray))
            ]
            if not columns:
                raise ValueError("表中无有效字段")

            # 构建并执行SQL查询
            selects = [f"COUNT(*) AS total"] + [
                f"{self._generate_null_sql(col)} AS {col}" for col in columns
            ]
            sql = text(f"SELECT {', '.join(selects)} FROM {self.table_name}")
            with self.engine.connect() as conn:
                result = conn.execute(sql).fetchone()

                # 生成控制台表格
            total = result.total if result else 0
            table = PrettyTable()
            table.field_names = ["字段名", "空值数量", "空值率", "状态描述"]
            table.align[" 字段名"] = "l"

            # 数据收集（用于文件输出）
            excel_data = []
            for col in columns:
                null_count = getattr(result, col) if result else 0
                null_rate = (null_count / total * 100) if total > 0 else 0
                desc = self._get_null_description(null_rate)

                # 填充控制台表格
                table.add_row([col, null_count, f"{null_rate:.1f}%", desc])
                # 收集Excel数据
                excel_data.append({" 字段名": col, "状态描述": desc})

            # 控制台输出
            print(f"\n[分析结果] 表名: {self.table_name}  | 总记录数: {total}")
            print(table)

            # 创建输出目录
            txt_dir = os.path.join("null", "files")
            excel_dir = os.path.join("null", "files", "excel")
            os.makedirs(txt_dir, exist_ok=True)
            os.makedirs(excel_dir, exist_ok=True)

            # 写入文本报告
            txt_path = os.path.join(txt_dir, f"null_analysis_{self.table_name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f" 生成时间: {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}\n")
                f.write(f" 数据库类型: {self.db_type.upper()}\n")
                f.write(f" 表名: {self.table_name}\n")
                f.write(f" 总记录数: {total}\n\n")
                f.write(str(table))
            print(f"\n✅ 文本报告已保存至: {os.path.abspath(txt_path)}")

            # 写入Excel文件
            excel_path = os.path.join(excel_dir, f"null_status_{self.table_name}.xlsx")
            pd.DataFrame(excel_data).to_excel(excel_path, index=False, engine="openpyxl")
            print(f"✅ 状态描述已导出至: {os.path.abspath(excel_path)}")

        except PermissionError as e:
            print(f"❌ 文件写入失败: 请检查目录权限 ({e})")
        except Exception as e:
            print(f"❌ 分析失败: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数据库空值分析工具")
    parser.add_argument("--db-type", required=True, choices=['mysql', 'oracle', 'postgresql'], help="数据库类型")
    parser.add_argument("--table", required=True, help="目标表名（区分大小写）")
    args = parser.parse_args()

    analyzer = NullAnalyzer(args.db_type, args.table)
    analyzer.analyze()
