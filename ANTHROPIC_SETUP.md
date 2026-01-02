# Anthropic Claude API Setup with Haiku 4.5

## Why Haiku 4.5?

**Claude Haiku 4.5** - Best choice for agent planning:
- **80% cheaper** than Sonnet ($0.80 vs $3.00 per M input tokens)
- **Faster** responses (~1-2 seconds)
- **Perfect for planning** - doesn't need Sonnet's power
- **$5 free credits = 10,000+ agent executions!**

## Pricing Comparison

| Model | Input | Output | Planning Cost |
|-------|-------|--------|---------------|
| Haiku 4.5 | $0.80/M | $4.00/M | $0.0005 |
| Sonnet 4 | $3.00/M | $15.00/M | $0.0021 |

**Haiku is 4x cheaper for planning!**

## Get Free API Credits

1. Go to https://console.anthropic.com
2. Sign up (no credit card required)
3. Get **$5 in free credits**
4. Go to Settings → API Keys
5. Create a new API key

## Set Up API Key
```bash
# Add to environment
export ANTHROPIC_API_KEY='your-api-key-here'

# Make it persistent
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

## Install Anthropic SDK
```bash
pip install --break-system-packages anthropic
```

## Test It
```bash
python3 examples/test_llm_planner.py
```

## What $5 Gets You

With Haiku 4.5:
- **10,000+ agent planning calls**
- Average: $0.0005 per plan
- Input: ~200 tokens = $0.00016
- Output: ~100 tokens = $0.00040

Perfect for development and testing!

## Monitor Usage

https://console.anthropic.com/settings/usage

## When to Use Each Model

- **Haiku 4.5**: Agent planning (our use case) ✓
- **Sonnet 4**: Complex reasoning, long context
- **Opus**: Most difficult tasks

For agentic_sdk planning, **Haiku is perfect!**
