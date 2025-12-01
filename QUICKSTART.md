# Quick Start Guide - Text2SQL with LangChain

Complete guide to run the project from scratch and see accuracy improvements.

## Prerequisites
- Docker Desktop installed and running
- Python 3.11+ (for local development)
- OpenAI API Key

## Step 1: Initial Setup (5 minutes)

### 1.1 Create Environment File
Create `.env` file in the project root:

```bash
# In project root directory
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
DB_USER=user
DB_PASS=password
DB_HOST=localhost
DB_PORT=5440
DB_NAME=text2sqldb
DB_NAME_DVD=dvdrental
EOF
```

**Important**: Replace `your_openai_api_key_here` with your actual OpenAI API key.

### 1.2 Verify Docker is Running
```bash
docker --version
docker compose version
```

## Step 2: Start the System (3 minutes)

### 2.1 Build and Start Containers
```bash
# Stop any existing containers
docker compose down

# Build and start fresh
docker compose up -d --build
```

This will:
- Start PostgreSQL with pgvector extension
- Create `dvdrental` and `text2sqldb` databases
- Start Streamlit web application
- Automatically run embedding initialization

### 2.2 Verify Containers are Running
```bash
docker ps
```

You should see:
- `text2sql-db` (PostgreSQL)
- `text2sql-web` (Streamlit)

### 2.3 Check Logs
```bash
# Check web container logs
docker logs text2sql-web

# Check database logs
docker logs text2sql-db
```

## Step 3: Generate Test Dataset (1 minute)

```bash
docker exec -it text2sql-web python /app/testset.py
```

Expected output:
```
✅ 테스트셋 생성 완료: experiments/dvdrental_testset.csv
📊 총 90개의 테스트 케이스
```

## Step 4: Access Streamlit UI

Open your browser and go to:
```
http://localhost:8501
```

You should see: **"📝 Text2SQL Demo with LangChain"**

## Step 5: Test the System

### Option A: Quick Test (Text2SQL Tab)
1. Click on **"Text2SQL"** tab
2. Enter a question: "배우는 총 몇 명인가요?"
3. Click **"Run"** button
4. You should see:
   - Generated SQL query
   - Query results in a table

### Option B: Full Accuracy Test (실험결과 1 Tab)
1. Click on **"실험결과 1"** tab
2. Scroll down to **"Base vs MapleRepair 비교"** section
3. Click **"비교 실행"** button
4. Wait for evaluation to complete (~5-10 minutes for 90 questions)
5. View results:
   - **Base EX**: Accuracy of base LangChain pipeline
   - **MapleRepair EX**: Accuracy with repair loop
   - Detailed comparison table

## Expected Results

### Before Improvements (Baseline)
- Base EX: ~31%
- MapleRepair EX: ~34%

### After Improvements (Current Version)
- Base EX: ~50-55% (expected)
- MapleRepair EX: ~55-60% (expected)

**Improvement**: +20-25% accuracy gain

## What Improvements Were Applied?

### 1. Enhanced Few-Shot Examples
Added 7 critical examples in `prompts/few_shot_examples.py`:
- NOT IN with DISTINCT
- Type casting with ::numeric
- LIKE pattern matching
- NULL handling with IS NULL
- Date casting with ::date
- ABS() for absolute values

### 2. Enhanced System Prompt
Added critical rules in `prompts/sql_generation_prompt.py`:
- Type casting rules (::numeric for division)
- NULL handling guidelines
- DISTINCT with JOINs rules
- Common mistakes to avoid

### 3. Improved Retrieval
Increased retrieval limit from 10 to 15 in `retrievers/db_retriever.py`

## Troubleshooting

### Issue: Port 8501 already in use
```bash
# Find and kill the process
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
ports:
  - "8502:8501"  # Use 8502 instead
```

### Issue: Database connection refused
```bash
# Restart containers
docker compose down
docker compose up -d

# Check database is ready
docker exec -it text2sql-db psql -U user -d dvdrental -c "SELECT COUNT(*) FROM actor;"
```

### Issue: No embeddings found
```bash
# Manually run embedding initialization
docker exec -it text2sql-web python /app/init/init_table_docs.py

# Verify embeddings
docker exec -it text2sql-db psql -U user -d text2sqldb -c "SELECT COUNT(*) FROM table_docs;"
```

Expected: 14 rows

### Issue: OpenAI API errors
```bash
# Check API key is set
docker exec -it text2sql-web python -c "import os; print(os.getenv('OPENAI_API_KEY'))"

# Should print your API key (not None)
```

## Advanced: Run Evaluation from Command Line

### Test on Sample Questions
```bash
docker exec -it text2sql-web python -u /app/experiments/compare_before_after_improvements.py
```

### Compare Base vs MapleRepair
```bash
docker exec -it text2sql-web python -u /app/experiments/compare_maple_vs_base.py
```

Results saved to: `experiments/evaluation/`

## Project Structure

```
Query-VendingMachine-Mungyu/
├── .env                          # Environment variables (create this)
├── docker-compose.yml            # Docker configuration
├── main.py                       # Streamlit UI
├── testset.py                    # Test dataset generator
├── chains/
│   ├── text_to_sql_chain.py     # Base LangChain pipeline
│   └── v_mungyu/
│       └── maple_repair_chain.py # MapleRepair with error correction
├── prompts/
│   ├── few_shot_examples.py     # Few-shot examples (IMPROVED)
│   └── sql_generation_prompt.py # System prompt (IMPROVED)
├── retrievers/
│   └── db_retriever.py          # Vector search retriever (IMPROVED)
├── utils/
│   ├── db_utils.py              # Database utilities
│   └── logging_utils.py         # Logging utilities
├── init/
│   └── init_table_docs.py       # Embedding initialization
├── experiments/
│   ├── dvdrental_testset.csv    # Generated test dataset
│   └── evaluation/              # Evaluation results
└── docs/
    ├── ACCURACY_IMPROVEMENT_GUIDE.md  # Detailed improvement guide
    └── COMPARISON_BASE_vs_MAPLEREPAIR.md  # Comparison documentation
```

## Key Files Modified for Improvements

1. **prompts/few_shot_examples.py**
   - Added 7 new examples covering edge cases
   - Total: 17 examples (was 10)

2. **prompts/sql_generation_prompt.py**
   - Added "CRITICAL Type Casting Rules" section
   - Added "NULL Handling" section
   - Added "DISTINCT with JOINs" section
   - Added "Common Mistakes to AVOID" section

3. **retrievers/db_retriever.py**
   - Increased `limit` from 10 to 15

## Next Steps

### 1. Analyze Results
After running evaluation, check:
```bash
# View latest results
ls -lt experiments/evaluation/

# Open CSV in Excel or pandas
docker exec -it text2sql-web python -c "
import pandas as pd
df = pd.read_csv('experiments/evaluation/improved_results_latest.csv')
print(df[df['match'] == False][['question', 'expected', 'result']].head(20))
"
```

### 2. Further Improvements
See `docs/ACCURACY_IMPROVEMENT_GUIDE.md` for:
- Phase 2: Advanced improvements (semantic validation)
- Phase 3: Data quality improvements (better table descriptions)
- Target: 70-80% accuracy

### 3. Customize for Your Use Case
- Add domain-specific examples to `few_shot_examples.py`
- Modify system prompt in `sql_generation_prompt.py`
- Adjust retrieval strategy in `db_retriever.py`

## Stopping the System

```bash
# Stop containers (keeps data)
docker compose stop

# Stop and remove containers (keeps volumes)
docker compose down

# Stop and remove everything including data
docker compose down -v
```

## Development Mode (Local)

If you want to run without Docker:

### 1. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Update .env for Local
```bash
DB_HOST=localhost
DB_PORT=5440  # Use mapped port
```

### 4. Run Streamlit Locally
```bash
streamlit run main.py
```

## Summary: Complete Restart Checklist

- [ ] Docker Desktop is running
- [ ] Created `.env` file with OpenAI API key
- [ ] Ran `docker compose down -v` (clean slate)
- [ ] Ran `docker compose up -d --build`
- [ ] Verified containers: `docker ps`
- [ ] Generated testset: `docker exec -it text2sql-web python /app/testset.py`
- [ ] Opened browser: `http://localhost:8501`
- [ ] Clicked "비교 실행" to see improved accuracy
- [ ] Results show ~50-55% accuracy (vs 31% baseline)

## Support

For issues or questions:
1. Check `docker logs text2sql-web` for errors
2. Review `docs/ACCURACY_IMPROVEMENT_GUIDE.md` for detailed explanations
3. Check `docs/COMPARISON_BASE_vs_MAPLEREPAIR.md` for methodology

---

**Last Updated**: 2025-11-25
**Version**: 2.0 (With Accuracy Improvements)
