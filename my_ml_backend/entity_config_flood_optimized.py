# -*- coding: utf-8 -*-
"""
洪涝灾害法律法规专门优化的命名实体识别配置文件
包含关系标签的实体化处理
"""

# 洪涝灾害专门的实体配置
FLOOD_NER_ENTITY_CONFIG = {
    # 🏛️ 法律条款与规范 (核心类型)
    "法律条款": {
        "description": "法律条款编号",
        "examples": ["第一条", "第十二条", "第1条", "第三章第二节", "第四十三条"],
        "category": "法律法规",
        "patterns": [
            r'第[一二三四五六七八九十百千万\d]+条',
            r'第[一二三四五六七八九十百千万\d]+章',
            r'第[一二三四五六七八九十百千万\d]+节',
            r'第[一二三四五六七八九十百千万\d]+款',
            r'第[一二三四五六七八九十百千万\d]+项',
            r'第[一二三四五六七八九十百千万\d]+编'
        ],
        "hotkey": "1",
        "invalid_patterns": []
    },
    "法律法规": {
        "description": "法律法规名称",
        "examples": ["《中华人民共和国防洪法》", "《水法》", "《防汛条例》", "《应急管理法》", "《突发事件应对法》"],
        "category": "法律法规",
        "patterns": [
            r'《[^》]*防洪[^》]*》',
            r'《[^》]*水法[^》]*》',
            r'《[^》]*防汛[^》]*》',
            r'《[^》]*应急[^》]*》',
            r'《[^》]*法》',
            r'《[^》]*条例》',
            r'《[^》]*办法》',
            r'《[^》]*规定》',
            r'《[^》]*预案》'
        ],
        "hotkey": "2",
        "invalid_patterns": []
    },
    "技术标准": {
        "description": "技术标准规范",
        "examples": ["国家标准", "行业标准", "地方标准", "技术规范", "设计标准", "安全标准"],
        "category": "法律法规",
        "patterns": [
            r'GB[/T]*\s*\d+',
            r'国家标准',
            r'行业标准',
            r'地方标准',
            r'技术规范',
            r'设计标准',
            r'安全标准'
        ],
        "invalid_patterns": []
    },
    "惩罚措施": {
        "description": "惩罚措施",
        "examples": ["罚款", "责令停产", "行政拘留", "刑事责任", "追究责任", "撤职", "警告", "没收违法所得"],
        "category": "法律法规",
        "patterns": [
            r'罚款\d+[万千]?元',
            r'责令.{1,10}',
            r'追究.{1,10}责任',
            r'行政拘留\d+日?',
            r'刑事责任',
            r'撤职',
            r'警告',
            r'没收.{1,10}'
        ],
        "invalid_patterns": []
    },
    
    # 🏢 政府机构与职责 (核心类型)
    "政府机构": {
        "description": "政府机构部门",
        "examples": ["国务院", "水利部", "应急管理部", "省政府", "市政府", "县政府"],
        "category": "机构组织",
        "patterns": [
            r'国务院',
            r'[国省市县区]政府',
            r'水利部',
            r'应急管理部',
            r'自然资源部',
            r'住房和城乡建设部',
            r'.+部',
            r'.+委员会',
            r'.+管理局',
            r'.+水利局'
        ],
        "hotkey": "3",
        "invalid_patterns": []
    },
    "防汛部门": {
        "description": "防汛专门部门",
        "examples": ["防汛抗旱指挥部", "防汛办", "水文站", "气象局", "河长办"],
        "category": "机构组织",
        "patterns": [
            r'防汛.{1,10}指挥部',
            r'防汛办',
            r'抗旱.{1,10}',
            r'水文站',
            r'气象局',
            r'河长办',
            r'流域管理.{1,10}'
        ],
        "invalid_patterns": []
    },
    "应急组织": {
        "description": "应急救援组织",
        "examples": ["应急救援队", "消防救援队", "武警部队", "民兵", "志愿者队伍"],
        "category": "机构组织",
        "patterns": [
            r'应急救援.{1,5}',
            r'消防救援.{1,5}',
            r'武警.{1,5}',
            r'民兵',
            r'志愿者.{1,5}',
            r'专业救援.{1,5}'
        ],
        "invalid_patterns": []
    },
    "职位职能": {
        "description": "职位职能",
        "examples": ["主要负责人", "防汛指挥", "应急管理", "水利管理", "安全监管", "总指挥"],
        "category": "机构组织",
        "patterns": [
            r'.{1,5}负责人',
            r'.{1,5}指挥',
            r'.{1,5}管理',
            r'.{1,5}监管',
            r'总指挥',
            r'副指挥',
            r'指挥长'
        ],
        "invalid_patterns": []
    },
    "责任主体": {
        "description": "责任主体",
        "examples": ["项目法人", "建设单位", "设计单位", "施工单位", "监理单位", "运行管理单位"],
        "category": "机构组织",
        "patterns": [
            r'项目法人',
            r'建设单位',
            r'设计单位',
            r'施工单位',
            r'监理单位',
            r'运行管理单位',
            r'业主单位'
        ],
        "invalid_patterns": []
    },
    
    # ⏰ 时间与预警 (核心类型)
    "时间节点": {
        "description": "具体时间节点",
        "examples": ["2023年5月15日", "2023-05-15", "上午9时", "72小时内", "立即"],
        "category": "时间",
        "patterns": [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d+时\d+分',
            r'\d+小时内',
            r'\d+日内',
            r'立即',
            r'紧急',
            r'马上'
        ],
        "hotkey": "4",
        "invalid_patterns": []
    },
    "预警等级": {
        "description": "预警等级",
        "examples": ["Ⅰ级预警", "红色预警", "橙色预警", "黄色预警", "蓝色预警"],
        "category": "时间",
        "patterns": [
            r'[ⅠⅡⅢⅣ一二三四]级预警',
            r'[红橙黄蓝]色预警',
            r'特大洪水',
            r'大洪水',
            r'中洪水',
            r'小洪水'
        ],
        "invalid_patterns": []
    },
    "应急时限": {
        "description": "应急响应时限",
        "examples": ["30分钟内", "2小时内", "24小时内", "72小时", "一周内"],
        "category": "时间",
        "patterns": [
            r'\d+分钟内',
            r'\d+小时内',
            r'\d+天内',
            r'\d+周内',
            r'\d+个月内'
        ],
        "invalid_patterns": []
    },
    "汛期时段": {
        "description": "汛期时段",
        "examples": ["汛期", "主汛期", "前汛期", "后汛期", "枯水期", "丰水期"],
        "category": "时间",
        "patterns": [
            r'汛期',
            r'主汛期',
            r'前汛期',
            r'后汛期',
            r'枯水期',
            r'丰水期',
            r'防汛期'
        ],
        "invalid_patterns": []
    },
    
    # 🌊 洪涝灾害要素 (专业类型)
    "灾害类型": {
        "description": "洪涝灾害类型",
        "examples": ["洪水", "内涝", "山洪", "泥石流", "滑坡", "堰塞湖", "溃坝"],
        "category": "灾害事件",
        "patterns": [
            r'洪水',
            r'内涝',
            r'山洪',
            r'泥石流',
            r'滑坡',
            r'堰塞湖',
            r'溃坝',
            r'决口',
            r'漫溢',
            r'渗漏'
        ],
        "hotkey": "5",
        "invalid_patterns": []
    },
    "水文要素": {
        "description": "水文要素",
        "examples": ["水位", "流量", "降雨量", "蒸发量", "径流", "洪峰"],
        "category": "灾害事件",
        "patterns": [
            r'水位',
            r'流量',
            r'降雨量',
            r'蒸发量',
            r'径流',
            r'洪峰',
            r'水量',
            r'库容',
            r'汇流'
        ],
        "invalid_patterns": []
    },
    "气象要素": {
        "description": "气象要素",
        "examples": ["降水", "暴雨", "台风", "强对流", "低压槽", "冷空气"],
        "category": "灾害事件",
        "patterns": [
            r'降水',
            r'暴雨',
            r'台风',
            r'强对流',
            r'低压槽',
            r'冷空气',
            r'气旋',
            r'锋面'
        ],
        "invalid_patterns": []
    },
    "灾害等级": {
        "description": "灾害等级",
        "examples": ["特别重大", "重大", "较大", "一般", "Ⅰ级", "Ⅱ级", "Ⅲ级", "Ⅳ级"],
        "category": "灾害事件",
        "patterns": [
            r'特别重大',
            r'重大',
            r'较大',
            r'一般',
            r'[ⅠⅡⅢⅣ一二三四]级',
            r'超标准洪水'
        ],
        "invalid_patterns": []
    },
    "影响范围": {
        "description": "影响范围",
        "examples": ["全流域", "上游", "中游", "下游", "左岸", "右岸", "城区", "农村"],
        "category": "灾害事件",
        "patterns": [
            r'全流域',
            r'上游',
            r'中游',
            r'下游',
            r'左岸',
            r'右岸',
            r'城区',
            r'农村',
            r'山区',
            r'平原'
        ],
        "invalid_patterns": []
    },
    
    # 🗺️ 地理位置与设施
    "水系河流": {
        "description": "水系河流",
        "examples": ["长江", "黄河", "珠江", "淮河", "海河", "松花江", "辽河"],
        "category": "地理信息",
        "patterns": [
            r'长江',
            r'黄河',
            r'珠江',
            r'淮河',
            r'海河',
            r'松花江',
            r'辽河',
            r'.{1,10}江',
            r'.{1,10}河',
            r'.{1,10}溪',
            r'.{1,10}湖'
        ],
        "hotkey": "6",
        "invalid_patterns": []
    },
    "行政区划": {
        "description": "行政区划",
        "examples": ["北京市", "河北省", "长江流域", "珠江流域", "城市建成区"],
        "category": "地理信息",
        "patterns": [
            r'.{1,10}省',
            r'.{1,10}市',
            r'.{1,10}县',
            r'.{1,10}区',
            r'.{1,10}流域',
            r'建成区',
            r'开发区'
        ],
        "invalid_patterns": []
    },
    "防洪设施": {
        "description": "防洪设施",
        "examples": ["水库", "大坝", "堤防", "护岸", "涵闸", "泵站", "分洪道"],
        "category": "地理信息",
        "patterns": [
            r'水库',
            r'大坝',
            r'堤防',
            r'护岸',
            r'涵闸',
            r'泵站',
            r'分洪道',
            r'行洪道',
            r'排水管网',
            r'雨水口'
        ],
        "invalid_patterns": []
    },
    "重要场所": {
        "description": "重要场所",
        "examples": ["学校", "医院", "养老院", "危化品仓库", "地下空间", "低洼地带"],
        "category": "地理信息",
        "patterns": [
            r'学校',
            r'医院',
            r'养老院',
            r'危化品仓库',
            r'地下空间',
            r'低洼地带',
            r'易涝点',
            r'重要设施'
        ],
        "invalid_patterns": []
    },
    
    # 🚨 应急响应与措施
    "应急预案": {
        "description": "应急预案",
        "examples": ["防汛应急预案", "山洪灾害预案", "城市内涝预案", "水库调度预案"],
        "category": "应急管理",
        "patterns": [
            r'防汛.{1,10}预案',
            r'山洪.{1,10}预案',
            r'内涝.{1,10}预案',
            r'应急预案',
            r'调度预案',
            r'抢险预案'
        ],
        "hotkey": "7",
        "invalid_patterns": []
    },
    "响应级别": {
        "description": "应急响应级别",
        "examples": ["Ⅰ级响应", "Ⅱ级响应", "Ⅲ级响应", "Ⅳ级响应"],
        "category": "应急管理",
        "patterns": [
            r'[ⅠⅡⅢⅣ一二三四]级响应',
            r'启动.{1,5}级响应',
            r'终止.{1,5}级响应'
        ],
        "invalid_patterns": []
    },
    "救援措施": {
        "description": "救援措施",
        "examples": ["人员搜救", "医疗救护", "生活救助", "心理援助", "应急供水", "应急供电"],
        "category": "应急管理",
        "patterns": [
            r'人员搜救',
            r'医疗救护',
            r'生活救助',
            r'心理援助',
            r'应急供水',
            r'应急供电',
            r'临时安置'
        ],
        "invalid_patterns": []
    },
    "疏散转移": {
        "description": "疏散转移",
        "examples": ["紧急疏散", "安全转移", "临时安置", "集中安置", "分散安置"],
        "category": "应急管理",
        "patterns": [
            r'紧急疏散',
            r'安全转移',
            r'临时安置',
            r'集中安置',
            r'分散安置',
            r'就近安置'
        ],
        "invalid_patterns": []
    },
    "抢险措施": {
        "description": "抢险措施",
        "examples": ["堵口复堤", "排水排涝", "加固护坡", "清障排险", "应急排险"],
        "category": "应急管理",
        "patterns": [
            r'堵口复堤',
            r'排水排涝',
            r'加固护坡',
            r'清障排险',
            r'应急排险',
            r'抢修道路',
            r'抢修电力'
        ],
        "invalid_patterns": []
    },
    
    # 📊 数值指标与标准
    "水位数据": {
        "description": "水位数据",
        "examples": ["警戒水位", "保证水位", "历史最高水位", "设计洪水位", "校核洪水位"],
        "category": "数值指标",
        "patterns": [
            r'警戒水位',
            r'保证水位',
            r'历史.{1,5}水位',
            r'设计.{1,5}水位',
            r'校核.{1,5}水位',
            r'\d+\.?\d*米',
            r'超.{1,5}水位'
        ],
        "hotkey": "8",
        "invalid_patterns": []
    },
    "流量数据": {
        "description": "流量数据",
        "examples": ["设计流量", "校核流量", "历史最大流量", "安全泄量"],
        "category": "数值指标",
        "patterns": [
            r'设计流量',
            r'校核流量',
            r'历史.{1,5}流量',
            r'安全泄量',
            r'\d+立方米每秒',
            r'\d+m³/s'
        ],
        "invalid_patterns": []
    },
    "降雨数据": {
        "description": "降雨数据",
        "examples": ["24小时降雨量", "日降雨量", "累积降雨量", "小时降雨强度"],
        "category": "数值指标",
        "patterns": [
            r'\d+小时降雨量',
            r'日降雨量',
            r'累积降雨量',
            r'降雨强度',
            r'\d+毫米',
            r'\d+mm'
        ],
        "invalid_patterns": []
    },
    "标准阈值": {
        "description": "标准阈值",
        "examples": ["防洪标准", "设计标准", "校核标准", "安全阈值"],
        "category": "数值指标",
        "patterns": [
            r'防洪标准',
            r'设计标准',
            r'校核标准',
            r'安全阈值',
            r'\d+年一遇',
            r'千年一遇',
            r'万年一遇'
        ],
        "invalid_patterns": []
    },
    "经济损失": {
        "description": "经济损失",
        "examples": ["直接经济损失", "间接经济损失", "财产损失", "损失评估"],
        "category": "数值指标",
        "patterns": [
            r'直接.{1,5}损失',
            r'间接.{1,5}损失',
            r'财产损失',
            r'损失评估',
            r'\d+[万千百]?元',
            r'\d+亿元'
        ],
        "invalid_patterns": []
    },
    
    # 🔍 监测预警系统
    "监测设备": {
        "description": "监测设备",
        "examples": ["水位计", "雨量计", "流量计", "视频监控", "自动站"],
        "category": "监测预警",
        "patterns": [
            r'水位计',
            r'雨量计',
            r'流量计',
            r'视频监控',
            r'自动站',
            r'遥测站',
            r'监测设备'
        ],
        "hotkey": "9",
        "invalid_patterns": []
    },
    "预警信号": {
        "description": "预警信号",
        "examples": ["暴雨预警", "洪水预警", "山洪预警", "地质灾害预警"],
        "category": "监测预警",
        "patterns": [
            r'暴雨预警',
            r'洪水预警',
            r'山洪预警',
            r'地质灾害预警',
            r'内涝预警',
            r'预警信号'
        ],
        "invalid_patterns": []
    },
    "信息发布": {
        "description": "信息发布",
        "examples": ["预警信息发布", "灾情信息发布", "应急广播", "手机短信"],
        "category": "监测预警",
        "patterns": [
            r'预警信息发布',
            r'灾情信息发布',
            r'应急广播',
            r'手机短信',
            r'网络发布',
            r'媒体发布'
        ],
        "invalid_patterns": []
    },
    "通信手段": {
        "description": "通信手段",
        "examples": ["卫星通信", "无线通信", "有线通信", "应急通信"],
        "category": "监测预警",
        "patterns": [
            r'卫星通信',
            r'无线通信',
            r'有线通信',
            r'应急通信',
            r'通信网络',
            r'通信设备'
        ],
        "invalid_patterns": []
    },
    
    # 💰 资源保障与物资
    "物资装备": {
        "description": "物资装备",
        "examples": ["抢险物资", "救生设备", "工程机械", "应急装备"],
        "category": "资源保障",
        "patterns": [
            r'抢险物资',
            r'救生设备',
            r'工程机械',
            r'应急装备',
            r'防汛物资',
            r'救援装备'
        ],
        "invalid_patterns": []
    },
    "资金保障": {
        "description": "资金保障",
        "examples": ["应急资金", "救灾资金", "防汛资金", "专项资金"],
        "category": "资源保障",
        "patterns": [
            r'应急资金',
            r'救灾资金',
            r'防汛资金',
            r'专项资金',
            r'资金保障',
            r'经费保障'
        ],
        "invalid_patterns": []
    },
    "人力资源": {
        "description": "人力资源",
        "examples": ["应急队伍", "专业队伍", "志愿者", "技术人员"],
        "category": "资源保障",
        "patterns": [
            r'应急队伍',
            r'专业队伍',
            r'志愿者',
            r'技术人员',
            r'救援人员',
            r'抢险队伍'
        ],
        "invalid_patterns": []
    },
    "技术支撑": {
        "description": "技术支撑",
        "examples": ["技术支撑", "专家咨询", "决策支持", "技术指导"],
        "category": "资源保障",
        "patterns": [
            r'技术支撑',
            r'专家咨询',
            r'决策支持',
            r'技术指导',
            r'技术服务',
            r'科技支撑'
        ],
        "invalid_patterns": []
    },
    
    # ⚖️ 监管执法与证据
    "执法措施": {
        "description": "执法措施",
        "examples": ["行政执法", "现场检查", "立案调查", "行政处罚"],
        "category": "监管执法",
        "patterns": [
            r'行政执法',
            r'现场检查',
            r'立案调查',
            r'行政处罚',
            r'执法检查',
            r'监督检查'
        ],
        "invalid_patterns": []
    },
    "违法行为": {
        "description": "违法行为",
        "examples": ["违法建设", "违法占用", "违法排污", "违法采砂"],
        "category": "监管执法",
        "patterns": [
            r'违法建设',
            r'违法占用',
            r'违法排污',
            r'违法采砂',
            r'违规.{1,10}',
            r'非法.{1,10}'
        ],
        "invalid_patterns": []
    },
    "证据材料": {
        "description": "证据材料",
        "examples": ["现场照片", "视频资料", "检测报告", "笔录材料"],
        "category": "监管执法",
        "patterns": [
            r'现场照片',
            r'视频资料',
            r'检测报告',
            r'笔录材料',
            r'证据材料',
            r'调查材料'
        ],
        "invalid_patterns": []
    },
    "整改要求": {
        "description": "整改要求",
        "examples": ["限期整改", "立即整改", "停止违法行为", "恢复原状"],
        "category": "监管执法",
        "patterns": [
            r'限期整改',
            r'立即整改',
            r'停止违法行为',
            r'恢复原状',
            r'整改措施',
            r'整改要求'
        ],
        "invalid_patterns": []
    },
    
    # 🔗 关系标签 (将关系转换为实体标签)
    "依据关系": {
        "description": "法律依据关系",
        "examples": ["根据", "依据", "按照", "遵照", "基于"],
        "category": "关系标签",
        "patterns": [
            r'根据.{1,20}',
            r'依据.{1,20}',
            r'按照.{1,20}',
            r'遵照.{1,20}',
            r'基于.{1,20}'
        ],
        "hotkey": "r",
        "invalid_patterns": []
    },
    "责任关系": {
        "description": "责任归属关系",
        "examples": ["负责", "主管", "承担责任", "负有责任", "应当"],
        "category": "关系标签",
        "patterns": [
            r'.{1,10}负责.{1,20}',
            r'.{1,10}主管.{1,20}',
            r'.{1,10}承担.{1,10}责任',
            r'.{1,10}负有.{1,10}责任',
            r'.{1,10}应当.{1,20}'
        ],
        "invalid_patterns": []
    },
    "管辖关系": {
        "description": "管辖权限关系",
        "examples": ["管辖", "管理", "监管", "统一领导", "归口管理"],
        "category": "关系标签",
        "patterns": [
            r'.{1,10}管辖.{1,20}',
            r'.{1,10}管理.{1,20}',
            r'.{1,10}监管.{1,20}',
            r'统一领导',
            r'归口管理'
        ],
        "invalid_patterns": []
    },
    "因果关系": {
        "description": "因果逻辑关系",
        "examples": ["导致", "造成", "引起", "产生", "由于"],
        "category": "关系标签",
        "patterns": [
            r'.{1,20}导致.{1,20}',
            r'.{1,20}造成.{1,20}',
            r'.{1,20}引起.{1,20}',
            r'.{1,20}产生.{1,20}',
            r'由于.{1,20}'
        ],
        "invalid_patterns": []
    },
    "时序关系": {
        "description": "时间先后关系",
        "examples": ["之前", "之后", "同时", "期间", "届时"],
        "category": "关系标签",
        "patterns": [
            r'.{1,20}之前',
            r'.{1,20}之后',
            r'.{1,20}同时',
            r'.{1,20}期间',
            r'届时.{1,20}'
        ],
        "invalid_patterns": []
    },
    "包含关系": {
        "description": "包含隶属关系",
        "examples": ["包括", "包含", "属于", "隶属", "组成"],
        "category": "关系标签",
        "patterns": [
            r'.{1,20}包括.{1,20}',
            r'.{1,20}包含.{1,20}',
            r'.{1,20}属于.{1,20}',
            r'.{1,20}隶属.{1,20}',
            r'.{1,20}组成'
        ],
        "invalid_patterns": []
    },
    "影响关系": {
        "description": "影响作用关系",
        "examples": ["影响", "受影响", "波及", "涉及", "关联"],
        "category": "关系标签",
        "patterns": [
            r'.{1,20}影响.{1,20}',
            r'.{1,20}受影响',
            r'.{1,20}波及.{1,20}',
            r'.{1,20}涉及.{1,20}',
            r'.{1,20}关联.{1,20}'
        ],
        "invalid_patterns": []
    },
    "协调关系": {
        "description": "协调配合关系",
        "examples": ["协调", "配合", "协作", "联合", "统筹"],
        "category": "关系标签",
        "patterns": [
            r'.{1,10}协调.{1,20}',
            r'.{1,10}配合.{1,20}',
            r'.{1,10}协作.{1,20}',
            r'.{1,10}联合.{1,20}',
            r'.{1,10}统筹.{1,20}'
        ],
        "invalid_patterns": []
    },
    "执行关系": {
        "description": "执行实施关系",
        "examples": ["执行", "实施", "落实", "贯彻", "推进"],
        "category": "关系标签",
        "patterns": [
            r'.{1,10}执行.{1,20}',
            r'.{1,10}实施.{1,20}',
            r'.{1,10}落实.{1,20}',
            r'.{1,10}贯彻.{1,20}',
            r'.{1,10}推进.{1,20}'
        ],
        "invalid_patterns": []
    },
    "补偿关系": {
        "description": "补偿赔偿关系",
        "examples": ["补偿", "赔偿", "补助", "救助", "资助"],
        "category": "关系标签",
        "patterns": [
            r'.{1,10}补偿.{1,20}',
            r'.{1,10}赔偿.{1,20}',
            r'.{1,10}补助.{1,20}',
            r'.{1,10}救助.{1,20}',
            r'.{1,10}资助.{1,20}'
        ],
        "invalid_patterns": []
    },
    
    # 🏥 疾病与健康
    "疾病类型": {
        "description": "疾病类型",
        "examples": ["霍乱", "痢疾", "肠道传染病", "水生疾病", "传染病", "流行病"],
        "category": "疾病健康",
        "patterns": [
            r'霍乱',
            r'痢疾',
            r'[传流].*病',
            r'肠道.*病',
            r'水.*病',
            r'疫情',
            r'病毒',
            r'细菌感染'
        ],
        "hotkey": "d",
        "invalid_patterns": []
    },
    "健康状况": {
        "description": "健康状况",
        "examples": ["身体状况", "健康状态", "受伤", "中毒", "感染", "病情"],
        "category": "疾病健康",
        "patterns": [
            r'身体.*状况',
            r'健康.*状态',
            r'受伤',
            r'中毒',
            r'感染',
            r'病情',
            r'伤情',
            r'症状'
        ],
        "invalid_patterns": []
    },
    "医疗需求": {
        "description": "医疗需求",
        "examples": ["医疗救助", "药品", "医疗设备", "救治", "急救", "医疗支援"],
        "category": "疾病健康",
        "patterns": [
            r'医疗.*救助',
            r'医疗.*支援',
            r'药品',
            r'医疗设备',
            r'救治',
            r'急救',
            r'医疗.*需求',
            r'卫生.*用品'
        ],
        "invalid_patterns": []
    },
    "防疫措施": {
        "description": "防疫措施",
        "examples": ["消毒", "疫苗", "隔离", "防疫", "卫生防护", "疾病预防"],
        "category": "疾病健康",
        "patterns": [
            r'消毒',
            r'疫苗',
            r'隔离',
            r'防疫',
            r'卫生.*防护',
            r'疾病.*预防',
            r'防疫.*措施',
            r'卫生.*消毒'
        ],
        "invalid_patterns": []
    },
    
    # 👥 人员信息
    "人员信息": {
        "description": "人员信息",
        "examples": ["张三", "李明，工程师", "男，45岁", "党员", "技术人员"],
        "category": "人员信息",
        "patterns": [
            r'[张李王刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段雷钱汤尹黎易常武乔贺赖龚文][一-龯]{1,3}',
            r'[男女]，\d+岁',
            r'党员',
            r'技术人员',
            r'工作人员',
            r'专业.*人员'
        ],
        "hotkey": "p",
        "invalid_patterns": []
    },
    "职务职称": {
        "description": "职务职称",
        "examples": ["高级工程师", "项目负责人", "指挥长", "副局长", "专业技术职称"],
        "category": "人员信息",
        "patterns": [
            r'[高中初]级.*工程师',
            r'.*负责人',
            r'.*指挥长',
            r'.*[局长科长处长]',
            r'.*职称',
            r'.*专家',
            r'.*主任',
            r'.*经理'
        ],
        "invalid_patterns": []
    },
    "专业技能": {
        "description": "专业技能",
        "examples": ["水利工程经验", "防汛技术", "专业能力", "技术特长", "工作经验"],
        "category": "人员信息",
        "patterns": [
            r'.*工程.*经验',
            r'.*技术',
            r'专业.*能力',
            r'技术.*特长',
            r'工作.*经验',
            r'.*专业.*技能',
            r'.*业务.*能力'
        ],
        "invalid_patterns": []
    },
    "联系方式": {
        "description": "联系方式",
        "examples": ["电话13912345678", "联系电话", "手机号码", "邮箱地址", "通信地址"],
        "category": "人员信息",
        "patterns": [
            r'[电联手]话?\d{11}',
            r'1[3-9]\d{9}',
            r'联系.*电话',
            r'手机.*号码',
            r'邮箱.*地址',
            r'通信.*地址',
            r'\w+@\w+\.\w+'
        ],
        "invalid_patterns": []
    },
    
    # 🔢 时间数量
    "时间数量": {
        "description": "时间数量",
        "examples": ["连续72小时", "48小时内", "3天时间", "时长6小时", "期限30天"],
        "category": "时间数量",
        "patterns": [
            r'连续\d+[小时天月年]',
            r'\d+[小时天月年]内',
            r'\d+[小时天月年]时间',
            r'时长\d+[小时天月年]',
            r'期限\d+[小时天月年]',
            r'\d+[个]?[小时天月年]'
        ],
        "hotkey": "t",
        "invalid_patterns": []
    },
    "持续时间": {
        "description": "持续时间",
        "examples": ["警报持续3天", "持续降雨", "连续工作", "持续监测", "延续至"],
        "category": "时间数量",
        "patterns": [
            r'持续\d+[小时天月年]',
            r'持续.*[降雨工作监测]',
            r'连续.*[工作监测]',
            r'延续.*至',
            r'.*持续.*'
        ],
        "invalid_patterns": []
    },
    "频率周期": {
        "description": "频率周期",
        "examples": ["每隔2小时", "每天一次", "定期检查", "周期性", "频繁"],
        "category": "时间数量",
        "patterns": [
            r'每隔\d+[小时天月年]',
            r'每[天周月年].*次',
            r'定期.*',
            r'周期性',
            r'频繁',
            r'间隔\d+[小时天月年]'
        ],
        "invalid_patterns": []
    },
    "数量规模": {
        "description": "数量规模",
        "examples": ["转移群众5000人", "投入资金", "物资数量", "规模庞大", "大量"],
        "category": "时间数量",
        "patterns": [
            r'转移.*\d+人',
            r'投入.*\d+[万千百]?[元人]',
            r'.*数量.*\d+',
            r'规模.*[庞大]',
            r'大量.*',
            r'\d+[万千百]?[人次台套件]'
        ],
        "invalid_patterns": []
    }
}

# 实体类别分组
FLOOD_ENTITY_CATEGORIES = {
    "法律法规": ["法律条款", "法律法规", "技术标准", "惩罚措施"],
    "机构组织": ["政府机构", "防汛部门", "应急组织", "职位职能", "责任主体"],
    "时间": ["时间节点", "预警等级", "应急时限", "汛期时段"],
    "灾害事件": ["灾害类型", "水文要素", "气象要素", "灾害等级", "影响范围"],
    "地理信息": ["水系河流", "行政区划", "防洪设施", "重要场所"],
    "应急管理": ["应急预案", "响应级别", "救援措施", "疏散转移", "抢险措施"],
    "数值指标": ["水位数据", "流量数据", "降雨数据", "标准阈值", "经济损失"],
    "监测预警": ["监测设备", "预警信号", "信息发布", "通信手段"],
    "资源保障": ["物资装备", "资金保障", "人力资源", "技术支撑"],
    "监管执法": ["执法措施", "违法行为", "证据材料", "整改要求"],
    "疾病健康": ["疾病类型", "健康状况", "医疗需求", "防疫措施"],
    "人员信息": ["人员信息", "职务职称", "专业技能", "联系方式"],
    "时间数量": ["时间数量", "持续时间", "频率周期", "数量规模"],
    "关系标签": ["依据关系", "责任关系", "管辖关系", "因果关系", "时序关系", 
                "包含关系", "影响关系", "协调关系", "执行关系", "补偿关系"]
}

def get_entity_config():
    """获取实体配置"""
    return FLOOD_NER_ENTITY_CONFIG

def get_entity_labels():
    """获取所有实体标签"""
    return list(FLOOD_NER_ENTITY_CONFIG.keys())

def get_all_categories():
    """获取所有类别"""
    return list(FLOOD_ENTITY_CATEGORIES.keys())

def get_entities_by_category(category):
    """根据类别获取实体"""
    if category in FLOOD_ENTITY_CATEGORIES:
        entities = {}
        for entity_name in FLOOD_ENTITY_CATEGORIES[category]:
            if entity_name in FLOOD_NER_ENTITY_CONFIG:
                entities[entity_name] = FLOOD_NER_ENTITY_CONFIG[entity_name]
        return entities
    return {}

def get_category_info(category):
    """获取类别信息"""
    if category in FLOOD_ENTITY_CATEGORIES:
        entities = FLOOD_ENTITY_CATEGORIES[category]
        return {
            "category": category,
            "entity_count": len(entities),
            "entities": entities
        }
    return None

def print_config_summary():
    """打印配置总结"""
    total_entities = len(FLOOD_NER_ENTITY_CONFIG)
    total_categories = len(FLOOD_ENTITY_CATEGORIES)
    
    print(f"🌊 洪涝灾害法律法规实体配置总结")
    print(f"   总实体数量: {total_entities}")
    print(f"   总类别数量: {total_categories}")
    print(f"   包含关系标签: 10个")
    print(f"   新增疾病健康: 4个")
    print(f"   新增人员信息: 4个")
    print(f"   新增时间数量: 4个")
    
    print(f"\n📋 类别分布:")
    for category, entities in FLOOD_ENTITY_CATEGORIES.items():
        print(f"   • {category}: {len(entities)} 个实体")
        
    print(f"\n🔥 重点特色:")
    print(f"   ✅ 专门针对洪涝灾害法律法规优化")
    print(f"   ✅ 将关系转换为实体标签，便于标注")
    print(f"   ✅ 保留详细的正则模式匹配")
    print(f"   ✅ 增加快捷键支持，提高标注效率")

if __name__ == "__main__":
    print_config_summary()
