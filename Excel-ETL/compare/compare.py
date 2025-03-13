import pymysql
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple


class TableDiffAnalyzer:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        self.prefix = "tb_czyth_gzc_"
        self.report_time = datetime(2025, 3, 13, 13, 57)  # 指定报告时间

    def _extract_comment_en(self, comment: str) -> str:
        """智能提取注释中的英文部分"""
        if not isinstance(comment, str):  # 处理空注释情况
            return ""
        return comment.split('--')[0].strip().lower()

    def fetch_tables(self) -> List[Dict]:
        """安全获取目标数据表"""
        try:
            with self.conn.cursor() as cursor:
                sql = """
                    SELECT TABLE_NAME, TABLE_COMMENT 
                    FROM information_schema.TABLES 
                    WHERE TABLE_NAME LIKE %s 
                    AND TABLE_SCHEMA = %s 
                """
                cursor.execute(sql, (f"{self.prefix}%", self.conn.db))
                return cursor.fetchall()
        except pymysql.Error as e:
            print(f"数据库查询失败: {str(e)}")
            return []

    def analyze_differences(self) -> Tuple[int, List[Dict]]:
        """执行增强版差异分析"""
        diff_details = []

        for table in self.fetch_tables():
            # 结构化处理数据
            raw_name = table['TABLE_NAME']
            short_name = raw_name[len(self.prefix):].lower() if raw_name.startswith(self.prefix) else ""
            comment_en = self._extract_comment_en(table['TABLE_COMMENT'])

            if not all([short_name, comment_en]):
                continue  # 跳过无效数据

            if short_name != comment_en:
                diff_details.append({
                    "原始表名": raw_name,
                    "处理后表名": short_name,
                    "注释英文名": comment_en,
                    "差异类型": self._get_diff_type(short_name, comment_en)
                })

        return len(diff_details), diff_details

    def _get_diff_type(self, name1: str, name2: str) -> str:
        """智能判断差异类型"""
        if '_' in name1 and '-' in name2:
            return "分隔符差异"
        if name1.replace('_', '') == name2.replace('_', ''):
            return "下划线位置差异"
        return "内容差异"

    def generate_report(self, count: int, details: List[Dict]):
        """生成双输出报告（控制台+Excel）"""
        # 控制台输出
        print(f"[{self.prefix}] 表名注释差异分析报告")
        print(f"报告时间：{self.report_time.strftime('%Y-%m-%d  %H:%M')}")
        print("▔" * 50)
        print(f"▶ 差异总数：{count}\n")

        if count > 0:
            print("📌 前20条差异示例：")
            sample = details[:20]
            for idx, item in enumerate(sample, 1):
                print(f"{idx}. {item['原始表名']}")
                print(f"   ▷ 表名部分：{item['处理后表名']}")
                print(f"   ▷ 注释部分：{item['注释英文名']}")
                print(f"   ▷ 差异类型：{item['差异类型']}\n")

        # Excel导出
        self._export_to_excel(details)

    def _export_to_excel(self, data: List[Dict]):
        """生成带格式的Excel报告"""
        try:
            timestamp = self.report_time.strftime("%Y%m%d_%H%M")
            filename = f"table_diff_report_{timestamp}.xlsx"

            df = pd.DataFrame(data)
            # 添加辅助列
            df['是否匹配'] = df.apply(lambda x: "否" if x['处理后表名'] != x['注释英文名'] else "是", axis=1)

            # 按指定列顺序排序
            column_order = [
                '原始表名', '处理后表名', '注释英文名',
                '是否匹配', '差异类型'
            ]
            df = df[column_order]

            # 使用Excel格式引擎
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='差异报告')
                # 获取工作表对象进行格式调整
                worksheet = writer.sheets[' 差异报告']
                # 设置列宽
                worksheet.column_dimensions['A'].width = 35  # 原始表名
                worksheet.column_dimensions['B'].width = 25  # 处理后表名
                worksheet.column_dimensions['C'].width = 25  # 注释英文名
                worksheet.column_dimensions['D'].width = 12  # 是否匹配

            print(f"\n✅ Excel报告已生成：{filename}")
        except Exception as e:
            print(f"\n❌ 导出失败：{str(e)}")


if __name__ == "__main__":
    # 初始化分析器（参数需替换）
    analyzer = TableDiffAnalyzer(
        host="10.10.10.215",
        port=3306,
        user="etladmin",
        password="etladmin123",
        database="HG_SourceDB"
    )

    try:
        total, details = analyzer.analyze_differences()
        analyzer.generate_report(total, details)
    finally:
        analyzer.conn.close()