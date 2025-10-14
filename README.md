# AgentCore Spec Generator

AWS Bedrock AgentCore를 사용하여 프로젝트 명세서를 자동 생성하는 HTTP 프로토콜 에이전트입니다.

## 주요 기능

- **프로젝트 명세서 자동 생성**: 프로젝트 이름, 설명, 기능 목록, 기술 스택을 입력하면 다음 문서들을 자동 생성합니다:
  - `10-requirements.md`: 요구사항 정의서
  - `20-architecture.md`: 아키텍처 설계서
  - `30-backlog.yaml`: 백로그 (스프린트별 작업 목록)
  - `trace.yaml`: 추적성 매트릭스

- **Claude 3.5 Sonnet 기반**: AWS Bedrock의 Claude 3.5 Sonnet v2 모델 사용
- **완전 관리형**: AWS Bedrock AgentCore로 자동 스케일링 및 고가용성 제공

## 아키텍처

```
Client → AWS Bedrock AgentCore (HTTP) → Spec Agent → Claude 3.5 Sonnet
```

- **Protocol**: HTTP
- **Runtime**: AWS Bedrock AgentCore
- **Model**: Claude 3.5 Sonnet v2 (APAC inference profile)
- **Memory**: STM (Short-term memory, 30일 보존)
- **Region**: ap-northeast-1

## 배포 정보

### 현재 배포된 Runtime

- **Agent Name**: specagent
- **ARN**: `arn:aws:bedrock-agentcore:ap-northeast-1:658886689642:runtime/specagent-Xl9a5QHYbF`
- **Memory ID**: specagent_mem-ONRrFBEq8q
- **ECR Repository**: `658886689642.dkr.ecr.ap-northeast-1.amazonaws.com/bedrock-agentcore-specagent`

### AWS Resources

- **Execution Role**: `AmazonBedrockAgentCoreSDKRuntime-ap-northeast-1-9ab9dc1e3f`
- **CodeBuild Project**: `bedrock-agentcore-specagent-builder`
- **S3 Source Bucket**: `bedrock-agentcore-codebuild-sources-658886689642-ap-northeast-1`

## 설치 및 실행

### 1. 환경 설정

```bash
# Python 가상환경 생성
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. AWS 자격증명 설정

```bash
# AWS Profile 설정 (ssu 프로필 사용)
export AWS_PROFILE=ssu
```

### 3. 에이전트 상태 확인

```bash
agentcore status
```

### 4. 에이전트 호출

#### Chat 예제
```bash
agentcore invoke '{"action": "chat", "prompt": "Hello!"}'
```

#### Spec 생성 예제
```bash
agentcore invoke '{
  "action": "generate_spec",
  "projectName": "E-Commerce Platform",
  "description": "온라인 쇼핑몰 플랫폼",
  "features": [
    "사용자 인증 및 권한 관리",
    "상품 카탈로그 관리",
    "장바구니 및 주문 처리",
    "결제 시스템 연동"
  ],
  "techStack": [
    "Frontend: React, TypeScript",
    "Backend: Node.js, Express",
    "Database: PostgreSQL, Redis",
    "Infrastructure: AWS, Docker"
  ]
}'
```

## 배포

### CodeBuild를 통한 배포 (권장)

```bash
# 코드 변경 후 재배포
agentcore launch
```

배포 프로세스:
1. CodeBuild에서 ARM64 컨테이너 빌드
2. ECR로 이미지 push
3. Bedrock AgentCore에 자동 배포
4. 런타임 엔드포인트 활성화

### 배포 모니터링

```bash
# CloudWatch 로그 확인
aws logs tail /aws/bedrock-agentcore/runtimes/specagent-Xl9a5QHYbF-DEFAULT \
  --log-stream-name-prefix "2025/10/14/[runtime-logs]" \
  --follow \
  --region ap-northeast-1
```

## API 명세

### Payload 구조

```json
{
  "action": "generate_spec",
  "projectName": "프로젝트 이름 (필수)",
  "description": "프로젝트 설명 (선택)",
  "features": ["기능1", "기능2"],
  "techStack": ["기술1", "기술2"]
}
```

### Response 구조

```json
{
  "success": true,
  "message": "Successfully generated spec documents for [프로젝트명]",
  "projectName": "프로젝트명",
  "files": {
    "requirements": {
      "path": "./specs/10-requirements.md",
      "content": "요구사항 문서 전체 내용",
      "size": 파일크기
    },
    "architecture": { ... },
    "backlog": { ... },
    "trace": { ... }
  }
}
```

## 프로젝트 구조

```
agentcore-spec/
├── .bedrock_agentcore.yaml  # AgentCore 설정 파일
├── .gitignore               # Git 제외 파일 목록
├── README.md                # 프로젝트 문서 (본 파일)
├── requirements.txt         # Python 의존성
└── spec_agent.py           # Spec 생성 에이전트 메인 소스
```

## 의존성

- `strands-agents`: AWS Bedrock AgentCore SDK
- `bedrock-agentcore`: AgentCore 런타임
- `boto3`: AWS SDK

## 모니터링

### CloudWatch Logs
- Runtime logs: `/aws/bedrock-agentcore/runtimes/specagent-Xl9a5QHYbF-DEFAULT`
- OTEL logs: `otel-rt-logs` 스트림

### GenAI Observability Dashboard
https://console.aws.amazon.com/cloudwatch/home?region=ap-northeast-1#gen-ai-observability/agent-core

### X-Ray Tracing
- 활성화됨
- CloudWatch Logs로 trace segment 전송

## 라이선스

Apache-2.0

## 작성자

AirDevOps Team
