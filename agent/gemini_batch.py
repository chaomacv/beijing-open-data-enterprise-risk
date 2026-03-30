import os
from openai import OpenAI
import json

# ================= 配置区域 =================
# 🚨 警告：你再次将真实的 API Key 贴在了代码里！
# 请务必去优云智算控制台重置这个 Key，避免被恶意盗刷导致欠费。
API_KEY = "JvSi87WwspUNYUEb72E3530b-18fA-4a7c-8196-C356F5C6"

# 直接使用文档推荐的统一通用端点
BASE_URL = "https://api.modelverse.cn/v1/" 
MODEL_NAME = "gemini-2.5-pro"  # 平台支持用 OpenAI 协议直接点名 Gemini

INPUT_FOLDER = "./input_jsons"
OUTPUT_FOLDER = "./output_results"

# 专门针对政务数据与组织机构的提取指令
TASK_REQUIREMENT = """
你是一个专业的政务数据分析与标签体系专家。你的任务是根据提供的【文件名】和【JSON 数据内容】，提取目标机构并为其打上精准的业务标签。请严格遵循以下规则处理数据：

### 规则一：目标群体过滤（只处理符合条件的实体）
1. 目标群体包含：机关、事业单位、社会团体、社会组织、民办非企业、基金会、人民团体、学校、医院、科研院所、律所、公证处、仲裁、协会、学会、商会、宗教活动场所、工会、社区、合作社，以及国有企业（如中建等）。
2. 排除群体：普通的个人、私营商业公司/工商企业。
3. 另外：
   - 文件中可能存在各种称呼的“统一社会信用代码”，但并不是所有的文件都存在。如果代码是以 `9` 开头，通常视为非目标群体（即普通私企），**必须剔除**。
   - 【豁免特例】：如果该实体代码虽然以 `9` 开头，但其名称明确属于“合作社”、“国有企业（如中字头、省市属国企）”、“公立医院”等，则予以保留，视作目标群体。

### 规则二：标签生成逻辑（文件名 + 数据内容）
1. 基础标签：首先从【文件名】中提取核心业务特征。例如文件名包含“示范基地”，则基础标签为“示范基地”。
2. 细化标签：必须阅读该实体在 JSON 中的具体字段内容进行补充。
   - 存在等级/级别字段时（如“三级甲等”、“4A”），需合并，如：“三级甲等互联网医保服务定点医疗机构”。
   - 存在状态/结果字段时（如“合格/不合格”、“A级/B级”、“红黑名单”），需区分，如：“行政检查不合格”、“信用良好A”。
   - 存在角色差异时，需区分，如：“对口帮扶项目单位”、“对口帮扶帮扶单位”。
3. 标签数量限制：针对同一份文件中的数据，提取出的总标签种类**不得超过 6 个**。通常一个实体只对应 1 个最精准的标签。

### 规则三：参考标签库（优先使用以下标签或进行合理变体）
奖，海外人才创业园，职业及从业者组织类社会团体，违法，二级甲等医疗机构，二级无等医疗机构，三级甲等医疗机构，三级无等医疗机构，一级无等医疗机构，一级甲等医疗机构，无等级医疗机构，普通养老机构，养老照料中心，行政处罚，三新及装备制造领域实验室，信用良好A，信用一般B，信用不良C，现代农业创新团队建设依托单位，科研机构，检查结果，处罚，示范，重点排污单位，示范站点，示范合作社，一级医院，二级医院，未评级医院，良好级标准化基地，优级标准化基地，达标级标准化基地，示范性工作室，先进单位，示范工程单位，定点医疗机构，定点零售药店，基本医疗保险A类定点医疗机构，行政检查不合格，市社科联所属社科类社会团体，市社科联所属民办社科研究机构，红黑名单，农产品生产主体，自然科学类学会协会基金会，科协金桥工程种子资金支持项目，区级中标，示范岗，示范基地，区医保局定点药店，养老机构，博士后科研平台，先进集体，农产品绿色食品认证，经开区绿色发展资金项目拟支持，京津冀协同创新推动项目，5A/4A/3A/2A/1A级社会组织，无等级社会组织，市级财政支持学前教育事业发展补助资金，阳光站，残疾人康复服务机构，婚前/孕前优生健康检查机构，示范村镇，乡村产业振兴人“头雁”，示范家庭农场，人力资源诚信服务示范单位，严重违法失信，社会组织年检不合格，社会组织活动异常，北京市民办残疾儿童康复服务定点机构，政府购买服务有关部门，具备星级资格社区养老服务驿站，建筑业新技术应用示范工程通过验收，生态农场，创新型绿色技术，残疾人福利基金会爱心榜，星创天地，对口帮扶项目单位，对口帮扶帮扶单位，科普惠农兴村计划，基层科普品牌活动支持计划，A级/B级/C级幼儿园。

### 输出格式要求
你必须且只能返回一个合法的 JSON 对象，不要包含任何额外的 Markdown 解释或说明（不要带有 ```json 标签）。JSON 格式如下：
{
  "file_name": "你接收到的文件名",
  "file_tags": ["标签1", "标签2"],
  "results": [
    {
      "entity_name": "提取出的机构名称",
      "credit_code": "提取出的统一社会信用代码（若有）",
      "tag": "赋予该机构的具体标签"
    }
  ],
  "filtered_out_count": 12
}
"""
# ============================================

def setup_folders():
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

def process_single_file(client, file_path, output_path):
    try:
        filename = os.path.basename(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            json_content = f.read() 
        
        print(f"⏳ 正在请求 API 处理: {filename} ...")

        # 【关键修复】：将文件名注入到 user_prompt 中，让模型能够提取基础标签
        user_prompt = f"当前处理的文件名为：【{filename}】\n\n请分析以下 JSON 数据：\n```json\n{json_content}\n```"

        # 使用最标准的 OpenAI completions 接口
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": TASK_REQUIREMENT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 简单清理模型可能附带的 Markdown json 标记，确保最终保存的是纯正 JSON
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # 保存为 .json 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_text)
            
        print(f"✅ 成功保存结果至: {output_path}")

    except Exception as e:
        print(f"❌ 处理失败: {e}")

def main():
    setup_folders()
    
    # 初始化客户端，注入平台配置
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

    for filename in os.listdir(INPUT_FOLDER):
        if filename.endswith(".json"):
            input_path = os.path.join(INPUT_FOLDER, filename)
            # 【修复】：将输出文件后缀改为 .json
            output_filename = filename.replace(".json", "_result.json")
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            # 断点续传逻辑
            if os.path.exists(output_path):
                print(f"⏭️ {output_filename} 已存在，跳过。")
                continue
                
            process_single_file(client, input_path, output_path)

if __name__ == "__main__":
    main()