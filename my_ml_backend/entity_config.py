# -*- coding: utf-8 -*-
"""
命名实体识别配置文件
基于Label Studio标签配置文件生成的实体类型定义
已优化：从139个标签精简为20个核心实体
"""

# 导入洪涝灾害专门优化的配置
from entity_config_flood_optimized import (
    FLOOD_NER_ENTITY_CONFIG as NER_ENTITY_CONFIG,
    get_entity_config, 
    get_entity_labels, 
    get_all_categories, 
    get_entities_by_category,
    FLOOD_ENTITY_CATEGORIES as ENTITY_CATEGORIES,
    get_category_info,
    print_config_summary
)

# 为了保持向后兼容性，这里重新导出所有需要的函数和变量
__all__ = [
    'NER_ENTITY_CONFIG',
    'get_entity_config',
    'get_entity_labels', 
    'get_all_categories',
    'get_entities_by_category',
    'ENTITY_CATEGORIES',
    'get_category_info',
    'print_config_summary'
]

# 主程序入口
if __name__ == "__main__":
    print("🌊 洪涝灾害法律法规专门优化的命名实体标签")
    print("=" * 70)
    print("📊 优化结果:")
    print("   • 原标签数量: 139个")
    print("   • 洪涝专门优化数量: 51个")
    print("   • 包含关系标签: 10个")
    print("   • 针对性优化程度: 高度专业化")
    
    print("\n🎯 洪涝灾害专门特色:")
    print("   ✅ 法律条款 (防洪法、水法等条款)")
    print("   ✅ 防汛部门 (防汛指挥部、水文站等)")
    print("   ✅ 水文要素 (水位、流量、降雨等)")
    print("   ✅ 灾害类型 (洪水、内涝、山洪等)")
    print("   ✅ 应急响应 (预警级别、救援措施等)")
    print("   ✅ 关系标签 (依据、责任、管辖等)")
    
    print("\n" + "=" * 70)
    print_config_summary()
    
    print("\n💡 标注建议:")
    print("   1. 使用快捷键提高标注效率 (数字键1-9, r键)")
    print("   2. 关系标签可标注动词短语，描述实体间关系")
    print("   3. 专业术语优先使用特定标签而非通用标签")
    print("   4. 法律条款标签支持多种格式识别")
    print("   5. 水文数据标签包含单位和数值模式")