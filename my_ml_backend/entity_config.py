# -*- coding: utf-8 -*-
"""
命名实体识别配置文件
基于Label Studio标签配置文件生成的实体类型定义
"""

# 完整的实体配置
NER_ENTITY_CONFIG = {
    # 文档类
    "文档类型": {
        "description": "文档类型",
        "examples": ["通知", "决定", "办法", "条例", "规定", "意见"],
        "category": "文档类",
        "invalid_patterns": []
    },
    "文档标题": {
        "description": "文档标题", 
        "examples": ["关于加强防汛工作的通知", "城市防洪管理办法", "应急预案"],
        "category": "文档类",
        "invalid_patterns": []
    },
    "发文机关": {
        "description": "发文机关",
        "examples": ["国务院", "水利部", "应急管理部", "省政府", "市政府"],
        "category": "文档类", 
        "invalid_patterns": []
    },
    "文号": {
        "description": "文号/文档编号",
        "examples": ["国发〔2023〕15号", "水防〔2023〕12号", "应急〔2023〕5号"],
        "category": "文档类",
        "valid_patterns": [r'〔\d+〕\d+号', r'\d+号文件']
    },
    "发布日期": {
        "description": "发布日期",
        "examples": ["2023年5月15日", "2023-05-15", "五月十五日"],
        "category": "文档类",
        "valid_patterns": [r'\d{4}年\d{1,2}月\d{1,2}日', r'\d{4}-\d{1,2}-\d{1,2}']
    },
    "生效日期": {
        "description": "生效日期",
        "examples": ["自发布之日起生效", "2023年6月1日起实施"],
        "category": "文档类",
        "invalid_patterns": []
    },
    "实施范围": {
        "description": "实施范围",
        "examples": ["全国范围", "长江流域", "珠江流域", "城市建成区"],
        "category": "文档类",
        "invalid_patterns": []
    },
    "版本号": {
        "description": "版本号/修订",
        "examples": ["第三版", "2023年修订版", "最新版"],
        "category": "文档类",
        "invalid_patterns": []
    },
    "附件": {
        "description": "附件/附录",
        "examples": ["附件1", "附录A", "技术规范"],
        "category": "文档类",
        "invalid_patterns": []
    },

    # 法律法规
    "法律法规": {
        "description": "法律法规",
        "examples": ["防洪法", "水法", "突发事件应对法", "安全生产法"],
        "category": "法律法规",
        "invalid_patterns": []
    },
    "法律条款": {
        "description": "法律条款",
        "examples": ["第二十三条", "第四章第二节", "条款三"],
        "category": "法律法规",
        "valid_patterns": [r'第.{1,5}条', r'第.{1,5}章']
    },
    "法律依据": {
        "description": "法律依据",
        "examples": ["根据防洪法规定", "依据水法", "按照应急管理条例"],
        "category": "法律法规",
        "invalid_patterns": []
    },
    "法律责任": {
        "description": "法律责任",
        "examples": ["承担法律责任", "行政责任", "刑事责任", "民事责任"],
        "category": "法律法规",
        "invalid_patterns": []
    },
    "处罚措施": {
        "description": "惩罚/处罚措施",
        "examples": ["罚款", "行政拘留", "吊销许可证", "责令停产"],
        "category": "法律法规",
        "invalid_patterns": []
    },
    "问责情况": {
        "description": "追责/问责情况",
        "examples": ["给予党纪处分", "免职处理", "通报批评", "诫勉谈话"],
        "category": "法律法规",
        "invalid_patterns": []
    },
    "诉讼": {
        "description": "诉讼/复议/仲裁",
        "examples": ["行政复议", "行政诉讼", "仲裁", "司法程序"],
        "category": "法律法规",
        "invalid_patterns": []
    },

    # 机构组织
    "机构组织": {
        "description": "机构组织",
        "examples": ["水利局", "应急管理局", "防汛指挥部", "气象局"],
        "category": "机构组织",
        "invalid_patterns": []
    },
    "责任主体": {
        "description": "责任主体",
        "examples": ["各级政府", "水库管理单位", "防汛责任人", "企业负责人"],
        "category": "机构组织",
        "invalid_patterns": []
    },
    "职位职能": {
        "description": "职位职能",
        "examples": ["总指挥", "副指挥", "技术负责人", "现场指挥员"],
        "category": "机构组织",
        "invalid_patterns": []
    },
    "人员": {
        "description": "人员/群体",
        "examples": ["工作人员", "技术专家", "抢险队员", "受灾群众"],
        "category": "机构组织",
        "invalid_patterns": []
    },
    "外部协作方": {
        "description": "外部协作方",
        "examples": ["消防部门", "武警部队", "社会救援组织", "志愿者"],
        "category": "机构组织",
        "invalid_patterns": []
    },

    # 地理信息
    "行政区划": {
        "description": "行政区划",
        "examples": ["北京市", "长江流域", "珠江三角洲", "华北地区"],
        "category": "地理信息",
        "invalid_patterns": []
    },
    "地理位置": {
        "description": "地理位置(地点名)",
        "examples": ["三峡大坝", "洞庭湖", "黄河下游", "太湖流域"],
        "category": "地理信息",
        "invalid_patterns": []
    },
    "区域信息": {
        "description": "区域信息(受灾/危险区)",
        "examples": ["洪泛区", "蓄滞洪区", "危险区域", "安全区"],
        "category": "地理信息",
        "invalid_patterns": []
    },
    "坐标": {
        "description": "坐标/GPS",
        "examples": ["北纬30°", "东经120°", "GPS坐标", "经纬度"],
        "category": "地理信息",
        "valid_patterns": [r'北纬\d+°', r'东经\d+°', r'GPS']
    },
    "流域": {
        "description": "流域/河段",
        "examples": ["长江中游", "黄河上游", "珠江流域", "淮河流域"],
        "category": "地理信息",
        "invalid_patterns": []
    },
    "防洪设施位置": {
        "description": "防洪设施位置",
        "examples": ["长江大堤", "黄河堤防", "水库坝址", "泵站位置"],
        "category": "地理信息",
        "invalid_patterns": []
    },

    # 灾害
    "灾害类型": {
        "description": "灾害类型",
        "examples": ["洪水", "暴雨", "台风", "干旱", "山洪", "泥石流"],
        "category": "灾害",
        "invalid_patterns": []
    },
    "灾害事件": {
        "description": "灾害事件",
        "examples": ["98洪水", "特大暴雨", "超强台风", "春旱"],
        "category": "灾害",
        "invalid_patterns": []
    },
    "溃坝": {
        "description": "溃坝/决口",
        "examples": ["堤防决口", "水库溃坝", "管涌", "滑坡"],
        "category": "灾害",
        "invalid_patterns": []
    },
    "事故后果": {
        "description": "事故后果",
        "examples": ["人员伤亡", "财产损失", "环境污染", "基础设施损坏"],
        "category": "灾害",
        "invalid_patterns": []
    },
    "影响范围": {
        "description": "影响范围",
        "examples": ["受灾面积", "影响人口", "淹没范围", "波及区域"],
        "category": "灾害",
        "invalid_patterns": []
    },

    # 时间
    "时间": {
        "description": "时间/日期/时段",
        "examples": ["汛期", "枯水期", "2023年7月", "凌晨3点"],
        "category": "时间",
        "valid_patterns": [r'\d+年\d+月', r'\d+点', r'汛期', r'枯水期']
    },
    "响应时间": {
        "description": "响应/启动时间",
        "examples": ["立即启动", "2小时内", "24小时内响应"],
        "category": "时间",
        "valid_patterns": [r'\d+小时内', r'\d+分钟内']
    },
    "处置时限": {
        "description": "处置时限/恢复期限",
        "examples": ["3天内完成", "一周内恢复", "30日内整改"],
        "category": "时间",
        "valid_patterns": [r'\d+天内', r'\d+周内', r'\d+日内']
    },

    # 数值指标
    "数值指标": {
        "description": "数值指标",
        "examples": ["降雨量", "水位", "流量", "库容", "100毫米"],
        "category": "数值指标",
        "valid_patterns": [r'\d+毫米', r'\d+立方米', r'\d+米']
    },
    "阈值": {
        "description": "阈值/警戒线",
        "examples": ["警戒水位", "保证水位", "设防标准", "50年一遇"],
        "category": "数值指标",
        "valid_patterns": [r'\d+年一遇', r'警戒', r'保证']
    },
    "预警级别": {
        "description": "灾害等级/预警级别",
        "examples": ["红色预警", "橙色预警", "I级响应", "特大洪水"],
        "category": "数值指标",
        "valid_patterns": [r'红色预警', r'橙色预警', r'I+级']
    },

    # 监测预警
    "监测站点": {
        "description": "监测站点/设备",
        "examples": ["水文站", "雨量站", "水位站", "监测点"],
        "category": "监测预警",
        "invalid_patterns": []
    },
    "预警信息": {
        "description": "预警/预报信息",
        "examples": ["暴雨预警", "洪水预报", "气象预报", "水情预报"],
        "category": "监测预警",
        "invalid_patterns": []
    },
    "预测模型": {
        "description": "预测模型/方法",
        "examples": ["数值预报模型", "统计预报", "人工智能预测"],
        "category": "监测预警",
        "invalid_patterns": []
    },

    # 应急响应
    "触发条件": {
        "description": "触发条件/启动条件",
        "examples": ["超过警戒水位", "预报降雨量达到", "发生险情"],
        "category": "应急响应",
        "invalid_patterns": []
    },
    "响应级别": {
        "description": "应急等级/响应级别",
        "examples": ["I级响应", "II级响应", "特别重大", "重大"],
        "category": "应急响应",
        "valid_patterns": [r'I+级响应', r'特别重大', r'重大']
    },
    "指挥体系": {
        "description": "指挥体系/指挥部",
        "examples": ["防汛指挥部", "应急指挥中心", "现场指挥部"],
        "category": "应急响应",
        "invalid_patterns": []
    },
    "处置措施": {
        "description": "处置措施/应对措施",
        "examples": ["人员转移", "工程抢险", "物资调配", "交通管制"],
        "category": "应急响应",
        "invalid_patterns": []
    },
    "决策": {
        "description": "决策/命令",
        "examples": ["启动预案", "下达指令", "紧急决定", "调度命令"],
        "category": "应急响应",
        "invalid_patterns": []
    },

    # 救援
    "疏散路线": {
        "description": "疏散路线/避难点",
        "examples": ["疏散路线", "避难场所", "临时安置点", "转移路径"],
        "category": "救援",
        "invalid_patterns": []
    },
    "救助措施": {
        "description": "安置/救助措施",
        "examples": ["临时安置", "生活救助", "医疗救护", "心理援助"],
        "category": "救援",
        "invalid_patterns": []
    },
    "救援力量": {
        "description": "救援力量/队伍",
        "examples": ["消防救援队", "武警部队", "专业救援队", "志愿者"],
        "category": "救援",
        "invalid_patterns": []
    },
    "物资装备": {
        "description": "物资/装备",
        "examples": ["救生衣", "冲锋舟", "发电机", "帐篷", "食品"],
        "category": "救援",
        "invalid_patterns": []
    },
    "物流运输": {
        "description": "物流/运输",
        "examples": ["物资运输", "直升机运送", "船只调配", "道路抢通"],
        "category": "救援",
        "invalid_patterns": []
    },

    # 基础设施
    "基础设施": {
        "description": "基础设施/关键设施",
        "examples": ["水库", "堤防", "泵站", "涵闸", "桥梁", "电力设施"],
        "category": "基础设施",
        "invalid_patterns": []
    },
    "设施状态": {
        "description": "设施状态/损坏情况",
        "examples": ["运行正常", "轻微损坏", "严重损毁", "功能失效"],
        "category": "基础设施",
        "invalid_patterns": []
    },
    "维修加固": {
        "description": "维修/加固措施",
        "examples": ["抢修", "加固", "临时修复", "紧急维护"],
        "category": "基础设施",
        "invalid_patterns": []
    },

    # 财政
    "资金保障": {
        "description": "资金/财政保障",
        "examples": ["救灾资金", "应急资金", "财政拨款", "专项资金"],
        "category": "财政",
        "invalid_patterns": []
    },
    "保险赔偿": {
        "description": "保险/赔偿",
        "examples": ["农业保险", "巨灾保险", "损失赔偿", "理赔"],
        "category": "财政",
        "invalid_patterns": []
    },
    "采购招标": {
        "description": "采购/招标/合同",
        "examples": ["政府采购", "公开招标", "应急采购", "合同签订"],
        "category": "财政",
        "invalid_patterns": []
    },

    # 证据
    "监测记录": {
        "description": "监测记录/报表",
        "examples": ["水情记录", "雨量记录", "巡查记录", "监测报告"],
        "category": "证据",
        "invalid_patterns": []
    },
    "证据材料": {
        "description": "照片/视频/证据材料",
        "examples": ["现场照片", "航拍视频", "卫星图像", "证据资料"],
        "category": "证据",
        "invalid_patterns": []
    },
    "证人证词": {
        "description": "目击证词/证人",
        "examples": ["目击者", "当事人", "证人证言", "现场证词"],
        "category": "证据",
        "invalid_patterns": []
    },

    # 监管
    "检查验收": {
        "description": "检查/验收/年检",
        "examples": ["安全检查", "汛前检查", "工程验收", "年度检查"],
        "category": "监管",
        "invalid_patterns": []
    },
    "隐患清单": {
        "description": "隐患/问题清单",
        "examples": ["安全隐患", "工程隐患", "问题清单", "风险点"],
        "category": "监管",
        "invalid_patterns": []
    },
    "监管措施": {
        "description": "监管措施/执法",
        "examples": ["执法检查", "监督检查", "行政执法", "违法查处"],
        "category": "监管",
        "invalid_patterns": []
    },

    # 培训
    "演练培训": {
        "description": "演练/培训",
        "examples": ["应急演练", "防汛演练", "培训教育", "技能培训"],
        "category": "培训",
        "invalid_patterns": []
    },
    "能力清单": {
        "description": "能力/资源清单",
        "examples": ["应急能力", "资源清单", "装备清单", "人员配置"],
        "category": "培训",
        "invalid_patterns": []
    },
    "预案条目": {
        "description": "应急预案条目/章节",
        "examples": ["应急预案", "操作规程", "技术方案", "实施细则"],
        "category": "培训",
        "invalid_patterns": []
    },

    # 灾后
    "恢复重建": {
        "description": "恢复与重建",
        "examples": ["灾后重建", "生产恢复", "基础设施重建", "家园重建"],
        "category": "灾后",
        "invalid_patterns": []
    },
    "善后保障": {
        "description": "善后保障/心理救援",
        "examples": ["善后处理", "心理疏导", "生活保障", "社会救助"],
        "category": "灾后",
        "invalid_patterns": []
    },
    "总结建议": {
        "description": "总结/教训/建议",
        "examples": ["工作总结", "经验教训", "改进建议", "对策建议"],
        "category": "灾后",
        "invalid_patterns": []
    },

    # 风险治理
    "风险评估": {
        "description": "风险评估/区划",
        "examples": ["风险评估", "洪水风险图", "风险区划", "脆弱性评估"],
        "category": "风险治理",
        "invalid_patterns": []
    },
    "设计标准": {
        "description": "设计标准/规范",
        "examples": ["设计标准", "技术规范", "建设标准", "安全标准"],
        "category": "风险治理",
        "invalid_patterns": []
    },
    "长期治理": {
        "description": "长期治理/适应",
        "examples": ["综合治理", "适应性管理", "可持续发展", "气候适应"],
        "category": "风险治理",
        "invalid_patterns": []
    },

    # 信息传播
    "联系人信息": {
        "description": "关键人/联系人信息",
        "examples": ["责任人电话", "联系方式", "值班电话", "紧急联系人"],
        "category": "信息传播",
        "valid_patterns": [r'\d{11}', r'\d{3,4}-\d{7,8}']
    },
    "发布渠道": {
        "description": "信息发布渠道",
        "examples": ["官方网站", "新闻发布会", "应急广播", "短信平台"],
        "category": "信息传播",
        "invalid_patterns": []
    },
    "媒体舆情": {
        "description": "媒体报道/舆情",
        "examples": ["新闻报道", "网络舆情", "社会关注", "媒体监督"],
        "category": "信息传播",
        "invalid_patterns": []
    },

    # 其他
    "跨界协同": {
        "description": "跨界/流域协同",
        "examples": ["跨区域协作", "流域统筹", "部门协调", "联防联控"],
        "category": "其他",
        "invalid_patterns": []
    },
    "政策变更": {
        "description": "法律/政策变更历史",
        "examples": ["政策调整", "法规修订", "制度变更", "标准更新"],
        "category": "其他",
        "invalid_patterns": []
    },
    "脆弱群体": {
        "description": "脆弱群体",
        "examples": ["老人儿童", "残疾人", "孕产妇", "重病患者"],
        "category": "其他",
        "invalid_patterns": []
    },
    "关键资产": {
        "description": "关键资产/经济设施",
        "examples": ["重要企业", "经济开发区", "关键基础设施", "文物古迹"],
        "category": "其他",
        "invalid_patterns": []
    },
    "模型算法": {
        "description": "模型/算法名称",
        "examples": ["洪水演进模型", "预报算法", "优化算法", "机器学习模型"],
        "category": "其他",
        "invalid_patterns": []
    },
    "数据来源": {
        "description": "数据来源/引用",
        "examples": ["监测数据", "统计年鉴", "调查数据", "文献资料"],
        "category": "其他",
        "invalid_patterns": []
    },

    # 关系类型（转为标签）
    "位于关系": {
        "description": "位于",
        "examples": ["位于长江流域", "坐落在", "地处"],
        "category": "关系",
        "invalid_patterns": []
    },
    "责任关系": {
        "description": "主管/责任",
        "examples": ["负责管理", "主管部门", "承担责任"],
        "category": "关系",
        "invalid_patterns": []
    },
    "因果关系": {
        "description": "触发/导致",
        "examples": ["导致洪水", "引发灾害", "造成损失"],
        "category": "关系",
        "invalid_patterns": []
    },
    "依据关系": {
        "description": "引用/依据",
        "examples": ["根据法律", "依据规定", "参照标准"],
        "category": "关系",
        "invalid_patterns": []
    },
    "包含关系": {
        "description": "包含/属于",
        "examples": ["包括内容", "属于范围", "涵盖方面"],
        "category": "关系",
        "invalid_patterns": []
    },
    "影响关系": {
        "description": "影响/受影响",
        "examples": ["影响区域", "受到冲击", "波及范围"],
        "category": "关系",
        "invalid_patterns": []
    },
    "隶属关系": {
        "description": "隶属/上下级",
        "examples": ["隶属于", "上级部门", "下属单位"],
        "category": "关系",
        "invalid_patterns": []
    },
    "发起关系": {
        "description": "发起/下达",
        "examples": ["发起行动", "下达命令", "启动程序"],
        "category": "关系",
        "invalid_patterns": []
    },
    "调配关系": {
        "description": "调配/支援",
        "examples": ["调配资源", "提供支援", "增援力量"],
        "category": "关系",
        "invalid_patterns": []
    },
    "检测关系": {
        "description": "检测/观测",
        "examples": ["监测水位", "观测降雨", "检测设备"],
        "category": "关系",
        "invalid_patterns": []
    },
    "补偿关系": {
        "description": "偿付/补偿",
        "examples": ["损失补偿", "经济赔偿", "费用偿付"],
        "category": "关系",
        "invalid_patterns": []
    },
    "整改关系": {
        "description": "整改/处理",
        "examples": ["限期整改", "问题处理", "措施落实"],
        "category": "关系",
        "invalid_patterns": []
    }
}

def get_entity_config():
    """获取实体配置"""
    return NER_ENTITY_CONFIG

def get_entity_labels():
    """获取所有实体标签列表"""
    return list(NER_ENTITY_CONFIG.keys())

def get_entities_by_category(category):
    """根据类别获取实体"""
    return {k: v for k, v in NER_ENTITY_CONFIG.items() if v.get('category') == category}

def get_all_categories():
    """获取所有类别"""
    categories = set()
    for config in NER_ENTITY_CONFIG.values():
        if 'category' in config:
            categories.add(config['category'])
    return sorted(list(categories))

# 打印配置统计信息
if __name__ == "__main__":
    print(f"总共配置了 {len(NER_ENTITY_CONFIG)} 种实体类型")
    categories = get_all_categories()
    print(f"包含 {len(categories)} 个类别:")
    for category in categories:
        entities = get_entities_by_category(category)
        print(f"  - {category}: {len(entities)} 个实体")
