# 🎵 Strands Music Research Demos

This folder contains various demonstration scripts showing different ways to use the Strands Music Research system.

## Available Demos

### 1. `mock_demo.py` - Mock Implementation (No API Required)
- **Purpose**: Demonstrates the architecture without requiring any API keys
- **Use Case**: Understanding the system flow and testing the architecture
- **Requirements**: None
- **Run**: `python demos/mock_demo.py`

### 2. `openai_correct_demo.py` - OpenAI Provider (Recommended)
- **Purpose**: Production-ready implementation using OpenAI as the LLM provider
- **Use Case**: Real-world usage with actual LLM capabilities
- **Requirements**: OpenAI API key
- **Setup**:
  ```bash
  pip install 'strands-agents[openai]'
  export OPENAI_API_KEY='your-api-key-here'
  ```
- **Run**: `python demos/openai_correct_demo.py`

### 3. `aws_bedrock_demo.py` - AWS Bedrock Provider
- **Purpose**: Uses AWS Bedrock with Claude models
- **Use Case**: AWS-integrated deployments
- **Requirements**: AWS credentials configured
- **Setup**:
  ```bash
  aws configure
  ```
- **Run**: `python demos/aws_bedrock_demo.py`

### 4. `simple_demo.py` - Simplified Example
- **Purpose**: Minimal implementation showing basic patterns
- **Use Case**: Learning the basics of Strands agents
- **Requirements**: Depends on provider configuration
- **Run**: `python demos/simple_demo.py`

### 5. `openai_demo.py` - Alternative OpenAI Implementation
- **Purpose**: Alternative approach to OpenAI integration
- **Use Case**: Testing different implementation patterns
- **Requirements**: OpenAI API key
- **Run**: `python demos/openai_demo.py`

## Demo Comparison

| Demo | API Required | Complexity | Best For |
|------|--------------|------------|----------|
| `mock_demo.py` | ❌ No | Low | Testing & Learning |
| `openai_correct_demo.py` | ✅ OpenAI | Medium | Production Use |
| `aws_bedrock_demo.py` | ✅ AWS | High | AWS Deployments |
| `simple_demo.py` | Varies | Low | Understanding Basics |
| `openai_demo.py` | ✅ OpenAI | Medium | Alternative Patterns |

## Quick Start

### For Testing (No API Key)
```bash
python demos/mock_demo.py
```

### For Production (With OpenAI)
```bash
export OPENAI_API_KEY='your-key-here'
python demos/openai_correct_demo.py
```

## Expected Output

All demos will:
1. Search for "deadmau5 - Strobe" across multiple platforms
2. Merge metadata from different sources
3. Assess quality and completeness
4. Find acquisition sources
5. Display results and save to JSON

## Troubleshooting

### OpenAI Demos
- Ensure `OPENAI_API_KEY` is set: `echo $OPENAI_API_KEY`
- Install OpenAI support: `pip install 'strands-agents[openai]'`

### AWS Bedrock Demo
- Configure AWS: `aws configure`
- Check credentials: `aws sts get-caller-identity`

### Mock Demo
- No configuration needed - should always work

## Architecture Notes

All demos follow the same multi-agent pattern:
- **DataCollector agents**: Platform-specific search
- **MetadataAnalyst**: Merges results
- **QualityAssessor**: Evaluates completeness
- **AcquisitionScout**: Finds purchase/stream options

The difference is mainly in the LLM provider configuration.