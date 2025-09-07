# -*- coding: utf-8 -*-
"""
🔥 森林火灾专用命名实体识别配置文件
专门针对森林防火领域优化的实体类型定义
覆盖法律法规、应急预案、技术标准等森林防火专业领域
"""

# 🔥 森林火灾专用实体配置
FOREST_FIRE_NER_ENTITY_CONFIG = {
    # 🏛️ 法律法规类
    "法律法规": {
        "description": "法律法规",
        "examples": ["森林防火条例", "森林法", "刑法", "森林防火规定"],
        "patterns": [r"《[^》]*森林[^》]*》", r"《[^》]*防火[^》]*》", r"《[^》]*条例》", r"《[^》]*法》"],
        "category": "法律法规"
    },
    "法律条款": {
        "description": "法律条款",
        "examples": ["第十条", "第三章", "第二节", "第四十二条"],
        "patterns": [r"第[一二三四五六七八九十百千万\d]+条", r"第[一二三四五六七八九十百千万\d]+章", r"第[一二三四五六七八九十百千万\d]+节"],
        "category": "法律法规"
    },
    "法律责任": {
        "description": "法律责任",
        "examples": ["刑事责任", "行政责任", "民事责任", "法律后果"],
        "patterns": [r"[刑行民]事责任", r"法律[责后][任果]", r"承担.*责任"],
        "category": "法律法规"
    },
    
    # 🏢 组织机构类
    "政府机构": {
        "description": "政府机构",
        "examples": ["县政府", "市林业局", "省应急厅", "森林公安"],
        "patterns": [r"[县市省区][^，。]*[政府局厅委办]", r"森林公安", r"林业[部局厅]"],
        "category": "组织机构"
    },
    "应急组织": {
        "description": "应急组织",
        "examples": ["应急指挥部", "现场指挥部", "扑火指挥组", "森林消防队"],
        "patterns": [r"[应急扑火森林]*指挥[部组]", r"森林消防[队伍]", r"[专业半]*扑火队"],
        "category": "组织机构"
    },
    "责任主体": {
        "description": "责任主体",
        "examples": ["森林经营单位", "林权所有者", "承包经营者", "管护责任人"],
        "patterns": [r"[森林]*经营[单位者]", r"林权[所有承包][者人]", r"责任[主体人]"],
        "category": "组织机构"
    },
    
    # 🔥 火灾防控类
    "火险等级": {
        "description": "火险等级",
        "examples": ["五级火险", "极高火险", "红色预警", "橙色预警"],
        "patterns": [r"[一二三四五1-5]级火险", r"[极高中低]*火险", r"[红橙黄蓝]色预警"],
        "category": "火灾防控"
    },
    "火源类型": {
        "description": "火源类型",
        "examples": ["人为火源", "自然火源", "雷击火", "用火不当"],
        "patterns": [r"[人为自然]*火源", r"雷击火", r"用火[不当违法]", r"[野外农事生产生活]用火"],
        "category": "火灾防控"
    },
    "火灾类型": {
        "description": "火灾类型",
        "examples": ["地表火", "树冠火", "地下火", "泥炭火"],
        "patterns": [r"[地表树冠地下泥炭]火", r"[surface crown ground].*火"],
        "category": "火灾防控"
    },
    
    # ⚙️ 技术设备类
    "防火设施": {
        "description": "防火设施",
        "examples": ["防火通道", "防火线", "消防蓄水池", "瞭望塔"],
        "patterns": [r"防火[通道线带隔离]", r"消防[设备池塔]", r"瞭望[塔台]", r"[监测预警]*设施"],
        "category": "技术设备"
    },
    "扑火装备": {
        "description": "扑火装备",
        "examples": ["风力灭火机", "水枪水炮", "化学灭火剂", "扑火工具"],
        "patterns": [r"[风力水泵化学].*灭火[机器剂]", r"扑火[工具装备器材]", r"[水枪炮泵]"],
        "category": "技术设备"
    },
    "监测设备": {
        "description": "监测设备",
        "examples": ["视频监控", "卫星遥感", "无人机", "传感器"],
        "patterns": [r"[视频红外]监控", r"卫星[遥感监测]", r"无人[机飞行器]", r"[温度湿度烟雾]传感器"],
        "category": "技术设备"
    },
    
    # 🚨 应急响应类
    "预警级别": {
        "description": "预警级别",
        "examples": ["蓝色预警", "黄色预警", "橙色预警", "红色预警"],
        "patterns": [r"[蓝黄橙红]色预警", r"[一二三四]级预警", r"[Ⅰ-Ⅳ]级预警"],
        "category": "应急响应"
    },
    "响应级别": {
        "description": "响应级别",
        "examples": ["一级响应", "二级响应", "三级响应", "四级响应"],
        "patterns": [r"[一二三四1-4]级响应", r"[Ⅰ-Ⅳ]级响应", r"[特重大较大一般]响应"],
        "category": "应急响应"
    },
    "应急措施": {
        "description": "应急措施",
        "examples": ["疏散转移", "交通管制", "停产停工", "封山禁火"],
        "patterns": [r"[疏散转移撤离]", r"[交通道路]管制", r"[停产工课]", r"[封山禁火令]"],
        "category": "应急响应"
    },
    
    # 🌡️ 气象环境类
    "气象要素": {
        "description": "气象要素",
        "examples": ["风向风速", "温度湿度", "降水量", "可燃物含水率"],
        "patterns": [r"[风向速力]", r"[温湿]度", r"降[水雨雪]量", r"含水[率量]", r"[干旱高温]"],
        "category": "气象环境"
    },
    "地理位置": {
        "description": "地理位置",
        "examples": ["林区", "山区", "保护区", "重点防火区"],
        "patterns": [r"[林山保护重点防火景区]区", r"[国家省市县级]*森林公园", r"[自然生态]保护区"],
        "category": "气象环境"
    },
    
    # 🔗 关系标签类
    "依据关系": {
        "description": "依据关系",
        "examples": ["根据", "依据", "按照", "遵循"],
        "patterns": [r"根据.*规定", r"依据.*条例", r"按照.*要求", r"遵循.*原则"],
        "category": "关系标签"
    },
    "责任关系": {
        "description": "责任关系", 
        "examples": ["负责", "主管", "承担", "履行"],
        "patterns": [r"负责.*工作", r"主管.*事务", r"承担.*责任", r"履行.*职责"],
        "category": "关系标签"
    },
    "因果关系": {
        "description": "因果关系",
        "examples": ["导致", "造成", "引起", "引发"],
        "patterns": [r"导致.*[后果损失]", r"造成.*[影响危害]", r"引[起发].*[火灾事故]"],
        "category": "关系标签"
    },
    "时序关系": {
        "description": "时序关系",
        "examples": ["之前", "之后", "期间", "同时"],
        "patterns": [r".*之[前后]", r".*期间", r"同时.*", r"随即.*", r"立即.*"],
        "category": "关系标签"
    },
    "协调关系": {
        "description": "协调关系", 
        "examples": ["协调", "配合", "联合", "协同"],
        "patterns": [r"协调.*[配合行动]", r"[联合协同].*[作战行动]", r"统一.*[指挥调度]"],
        "category": "关系标签"
    }
}

# 🔥 森林火灾实体类别定义
FOREST_FIRE_ENTITY_CATEGORIES = {
    "法律法规": {
        "description": "法律法规文件、条款、责任等",
        "entities": ["法律法规", "法律条款", "法律责任"],
        "icon": "🏛️"
    },
    "组织机构": {
        "description": "政府部门、应急组织、责任主体等",
        "entities": ["政府机构", "应急组织", "责任主体"],
        "icon": "🏢"
    },
    "火灾防控": {
        "description": "火险等级、火源类型、火灾类型等",
        "entities": ["火险等级", "火源类型", "火灾类型"],
        "icon": "🔥"
    },
    "技术设备": {
        "description": "防火设施、扑火装备、监测设备等",
        "entities": ["防火设施", "扑火装备", "监测设备"],
        "icon": "⚙️"
    },
    "应急响应": {
        "description": "预警级别、响应级别、应急措施等",
        "entities": ["预警级别", "响应级别", "应急措施"],
        "icon": "🚨"
    },
    "气象环境": {
        "description": "气象要素、地理位置等",
        "entities": ["气象要素", "地理位置"],
        "icon": "🌡️"
    },
    "关系标签": {
        "description": "表示实体间语义关系的词汇",
        "entities": ["依据关系", "责任关系", "因果关系", "时序关系", "协调关系"],
        "icon": "🔗"
    }
}

def get_entity_config():
    """获取森林火灾专用实体配置"""
    return FOREST_FIRE_NER_ENTITY_CONFIG

def get_entity_labels():
    """获取所有森林火灾实体标签列表"""
    return list(FOREST_FIRE_NER_ENTITY_CONFIG.keys())

def get_all_categories():
    """获取所有森林火灾实体类别"""
    return list(FOREST_FIRE_ENTITY_CATEGORIES.keys())

def get_entities_by_category(category):
    """根据类别获取森林火灾实体"""
    if category in FOREST_FIRE_ENTITY_CATEGORIES:
        entities = FOREST_FIRE_ENTITY_CATEGORIES[category]["entities"]
        return {entity: FOREST_FIRE_NER_ENTITY_CONFIG[entity] for entity in entities if entity in FOREST_FIRE_NER_ENTITY_CONFIG}
    return {}

def get_category_info(category):
    """获取森林火灾类别信息"""
    return FOREST_FIRE_ENTITY_CATEGORIES.get(category, {})

def print_config_summary():
    """打印森林火灾配置总结"""
    print("🔥 森林火灾专用实体配置总结:")
    print(f"   总实体数: {len(FOREST_FIRE_NER_ENTITY_CONFIG)}")
    print(f"   总类别数: {len(FOREST_FIRE_ENTITY_CATEGORIES)}")
    
    for category, info in FOREST_FIRE_ENTITY_CATEGORIES.items():
        entity_count = len(info["entities"])
        print(f"   {info['icon']} {category}: {entity_count} 个实体")

if __name__ == "__main__":
    print("🔥 森林火灾专用实体配置加载测试")
    print_config_summary()
    print("✅ 森林火灾配置文件正常")
