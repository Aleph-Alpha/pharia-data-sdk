# Contributing to pharia-data-sdk

## Development Setup

### Prerequisites
- [uv](https://docs.astral.sh/uv/)
- Python 3.12

### Local Development Setup

```bash
git clone https://github.com/aleph-alpha/pharia-data-sdk.git
cd pharia-data-sdk
```

####  Install dependencies
```bash
uv venv
uv sync
uv run pre-commit install
```

#### Setup environment variables

```bash
cp .env.example .env
```

### Running Tests

```bash
uv run pytest
```