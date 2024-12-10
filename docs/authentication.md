# Authentication

Before using the SWE-bench CLI, you'll need to set up authentication using an API key.

## Getting an API Key

1. Generate a new API key using your email:

```bash
sb-cli gen-api-key your.email@example.com
```

2. The CLI will output your API key. Save this key somewhere safe - you'll need it for all future operations.

## Setting Up Your API Key

There are two ways to use your API key:

### 1. Environment Setup (Recommended)

Set your API key as an environment variable:

```bash
export SWEBENCH_API_KEY=your_api_key
```

For permanent setup, add this line to your shell's configuration file (`.bashrc`, `.zshrc`, etc.).

!!! note
    You can test that your key is working with `sb-cli get-quotas`

### 2. Command Line Option

Alternatively, you can pass your API key directly with each command:

```bash
sb-cli submit --api_key your_api_key ...
```

## Verifying Your API Key

After receiving your API key, you'll get an email with a verification code. Verify your API key using:

```bash
sb-cli verify-api-key YOUR_VERIFICATION_CODE
```
