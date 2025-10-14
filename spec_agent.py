"""
AgentCore HTTP Agent with Spec Generation
Provides project specification document generation using AWS Bedrock Claude
"""

from bedrock_agentcore import BedrockAgentCoreApp
import boto3
import json
import os

# Initialize app
app = BedrockAgentCoreApp()

# Entrypoint for HTTP invocation
@app.entrypoint
def invoke(payload):
    """
    HTTP invocation entrypoint

    Supports two actions:
    1. chat - Simple conversation
    2. generate_spec - Generate project specification documents

    Payload structure:
    {
        "action": "chat" | "generate_spec",
        "prompt": "for chat action",
        "projectName": "for generate_spec action (required)",
        "description": "optional project description",
        "features": ["feature1", "feature2"],
        "techStack": ["tech1", "tech2"],
        "outputDir": "./specs"
    }
    """
    action = payload.get("action", "chat")

    if action == "generate_spec":
        return generate_project_spec(payload)
    else:
        # Default chat response
        prompt = payload.get("prompt", "No prompt provided")
        response = f"Hello! You said: '{prompt}'\n\n"
        response += "I'm an AgentCore HTTP agent with spec generation capabilities!\n\n"
        response += "Available actions:\n"
        response += "- chat: Have a conversation with me\n"
        response += "- generate_spec: Generate project specification documents\n\n"
        response += "Example spec generation:\n"
        response += '{"action": "generate_spec", "projectName": "My Project", "description": "A cool project", "features": ["Feature 1"], "techStack": ["Python"]}'

        return {"result": response}


def generate_project_spec(payload):
    """
    Generate project specification documents

    Returns:
        dict: Generation result with success status and files
    """
    project_name = payload.get("projectName")
    if not project_name:
        return {
            "success": False,
            "error": "projectName is required for generate_spec action"
        }

    description = payload.get("description", "")
    features = payload.get("features", [])
    tech_stack = payload.get("techStack", [])
    output_dir = payload.get("outputDir", "./specs")

    print(f"[INFO] Starting spec generation for: {project_name}")

    try:
        # Initialize Bedrock Runtime client
        # AWS SDK will automatically use IAM role credentials when running in ECS/Lambda
        # No need to specify profile - uses execution role from AgentCore
        bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-1')

        # Build project context
        context = build_project_context(project_name, description, features, tech_stack)

        print("[INFO] Generating requirements document...")
        requirements = generate_requirements(bedrock, context)

        print("[INFO] Generating architecture document...")
        architecture = generate_architecture(bedrock, context)

        print("[INFO] Generating backlog...")
        backlog = generate_backlog(bedrock, context, requirements)

        print("[INFO] Generating traceability matrix...")
        trace = generate_trace(bedrock, context, requirements, architecture, backlog)

        print("[INFO] Spec generation completed successfully")

        return {
            "success": True,
            "message": f"Successfully generated spec documents for {project_name}",
            "projectName": project_name,
            "files": {
                "requirements": {
                    "path": f"{output_dir}/10-requirements.md",
                    "content": requirements,
                    "size": len(requirements)
                },
                "architecture": {
                    "path": f"{output_dir}/20-architecture.md",
                    "content": architecture,
                    "size": len(architecture)
                },
                "backlog": {
                    "path": f"{output_dir}/30-backlog.md",
                    "content": backlog,
                    "size": len(backlog)
                },
                "trace": {
                    "path": f"{output_dir}/trace.yaml",
                    "content": trace,
                    "size": len(trace)
                }
            }
        }

    except Exception as e:
        print(f"[ERROR] Spec generation failed: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate spec: {str(e)}"
        }


def build_project_context(project_name, description, features, tech_stack):
    """Build project context string"""
    context = f"프로젝트 이름: {project_name}\n"

    if description:
        context += f"\n프로젝트 설명:\n{description}\n"

    if features:
        context += f"\n주요 기능:\n"
        for feature in features:
            context += f"- {feature}\n"

    if tech_stack:
        context += f"\n기술 스택:\n"
        for tech in tech_stack:
            context += f"- {tech}\n"

    return context


def invoke_bedrock_claude(bedrock, prompt):
    """Invoke Bedrock Claude model using APAC inference profile"""
    # Use APAC cross-region inference profile for Claude 3.5 Sonnet v2
    # This allows routing across multiple AP regions for better availability
    # AWS SDK automatically uses IAM role credentials in AgentCore runtime
    response = bedrock.invoke_model(
        modelId='apac.anthropic.claude-3-5-sonnet-20241022-v2:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        })
    )

    result = json.loads(response['body'].read())
    return result['content'][0]['text']


def generate_requirements(bedrock, context):
    """Generate requirements document"""
    prompt = f"""다음 프로젝트의 요구사항 문서를 작성해주세요:

{context}

Markdown 형식으로 다음 섹션을 포함해주세요:

# Requirements Document

## 1. 프로젝트 개요
프로젝트의 전반적인 목적과 배경을 설명합니다.

## 2. 목표
프로젝트가 달성하고자 하는 구체적인 목표를 나열합니다.

## 3. 기능 요구사항
각 기능 요구사항에 다음 형식으로 ID를 부여해주세요:
- REQ-F-001: 첫 번째 기능 요구사항
- REQ-F-002: 두 번째 기능 요구사항
각 요구사항은 명확하고 측정 가능하며 우선순위(High/Medium/Low)를 포함합니다.

## 4. 비기능 요구사항
각 비기능 요구사항에 다음 형식으로 ID를 부여해주세요:
- REQ-NF-001: 첫 번째 비기능 요구사항 (성능, 보안, 확장성 등)
- REQ-NF-002: 두 번째 비기능 요구사항

## 5. 제약사항
프로젝트의 제약사항과 한계를 명시합니다.

## 6. 가정사항
프로젝트 진행을 위한 가정사항을 나열합니다.
"""

    return invoke_bedrock_claude(bedrock, prompt)


def generate_architecture(bedrock, context):
    """Generate architecture document"""
    prompt = f"""다음 프로젝트의 아키텍처 문서를 작성해주세요:

{context}

Markdown 형식으로 다음 섹션을 포함해주세요:

# Architecture Document

## 1. 시스템 개요
시스템의 전반적인 구조와 핵심 개념을 설명합니다.

## 2. 시스템 컨텍스트
시스템이 외부 시스템 및 사용자와 어떻게 상호작용하는지 설명합니다.

## 3. 컴포넌트 구조
각 컴포넌트에 다음 형식으로 ID를 부여해주세요:
- COMP-001: Frontend Layer
- COMP-002: Backend API
- COMP-003: Database Layer
각 컴포넌트의 책임, 기술, 의존성을 명시합니다.

## 4. 데이터 흐름
주요 데이터 흐름과 처리 과정을 설명합니다.

## 5. 기술 스택 상세
Frontend, Backend, Database, Infrastructure 등으로 분류하여 상세히 설명합니다.

## 6. 배포 전략
배포 방식, 환경 구성, CI/CD 파이프라인을 설명합니다.

## 7. 보안 고려사항
인증, 인가, 데이터 보호 등 보안 측면을 다룹니다.
"""

    return invoke_bedrock_claude(bedrock, prompt)


def generate_backlog(bedrock, context, requirements):
    """Generate backlog in Markdown format"""
    prompt = f"""다음 프로젝트의 백로그를 Markdown 형식으로 작성해주세요:

프로젝트 정보:
{context}

요구사항 (참고용):
{requirements[:2000]}

Markdown 형식으로 다음 구조를 따라주세요:

# 프로젝트 백로그

## 프로젝트: [프로젝트 이름]

---

## Sprint 1: 기반 구축
**기간**: 2025-10-15 ~ 2025-10-28 (2주)

### Epic: [Epic 제목] (EPIC-001)
**우선순위**: High | **상태**: Todo | **예상**: 80h

#### User Stories

##### STORY-001: [스토리 제목]
- **설명**: 스토리 상세 설명
- **Type**: Story
- **우선순위**: High
- **상태**: Todo
- **예상 시간**: 40h
- **태그**: `backend`, `api`
- **의존성**: 없음

**인수 기준**:
- [ ] 인수 기준 1
- [ ] 인수 기준 2
- [ ] 인수 기준 3

**Tasks**:
- [ ] **TASK-001**: Task 제목 (8h)
- [ ] **TASK-002**: Task 제목 (16h)
- [ ] **TASK-003**: Task 제목 (16h)

---

각 Sprint는 2주 분량의 작업으로 구성하고, 요구사항과 연계된 백로그 항목들을 생성해주세요.
Epic → User Story → Task 계층으로 구조화하고, 의존성 관계를 명시해주세요.
체크박스 형식으로 작성하여 진행상황을 추적할 수 있게 해주세요.
"""

    return invoke_bedrock_claude(bedrock, prompt)


def generate_trace(bedrock, context, requirements, architecture, backlog):
    """Generate traceability matrix YAML"""
    prompt = f"""다음 프로젝트의 추적성 매트릭스를 YAML 형식으로 작성해주세요:

프로젝트 정보:
{context}

이 매트릭스는 요구사항 ID, 아키텍처 컴포넌트 ID, 백로그 항목 ID 간의 관계를 명시합니다.

YAML 형식으로 다음 구조를 따라주세요:

projectName: "프로젝트 이름"
traces:
  - requirementId: "REQ-F-001"
    requirementTitle: "요구사항 제목"
    architectureComponents:
      - "COMP-001"
      - "COMP-002"
    backlogItems:
      - "BACK-001"
      - "BACK-002"
    testCases:
      - "TEST-001"

  - requirementId: "REQ-F-002"
    requirementTitle: "두 번째 요구사항"
    architectureComponents:
      - "COMP-003"
    backlogItems:
      - "BACK-003"
    testCases:
      - "TEST-002"

요구사항, 아키텍처, 백로그 문서에서 추출한 ID들을 사용하여 매핑을 생성해주세요.
각 요구사항이 어떤 컴포넌트에서 구현되고, 어떤 백로그 항목과 연결되는지 명확히 해주세요.
"""

    return invoke_bedrock_claude(bedrock, prompt)


if __name__ == "__main__":
    app.run()
