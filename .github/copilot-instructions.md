# Project: PROJETO_COMISSOES_V2

## 🏗 Architecture & Core Components
- **Hybrid System**: Python backend (calculation engine) + React frontend (visualization).
- **Entry Point**: `calculo_comissoes.py` is the main orchestrator. It handles data loading, validation, calculation logic, and output generation.
- **Modularization Strategy**: The project is migrating logic to `src/`.
  - `src/currency`: Centralized currency conversion logic (uses `data/currency_rates/monthly_avg_rates.json`).
  - `src/io`: Data loading and configuration management (`ConfigLoader`, `DataLoader`).
  - `src/recebimento`: Logic for payment-based commissions.
  - `auditoria_pdf/`: Dedicated module for generating audit PDFs using ReportLab.
- **Frontend Adapter**: `frontend/adapter/app.py` (FastAPI) acts as a bridge, executing the Python scripts via subprocesses to serve the React UI.

## 🔄 Data Flow & Pipelines
1.  **Input**: Excel files placed in `dados_entrada/` (e.g., `Analise_Comercial_Completa.xlsx`, `Análise Financeira.xlsx`).
2.  **Preparation**: `preparar_dados_mensais.py` is automatically triggered to generate intermediate files (`Faturados.xlsx`, `Conversões.xlsx`, `Faturados_YTD.xlsx`).
3.  **Calculation**:
    - **Billing Commission**: Calculated item-by-item based on sales.
    - **Receipt Commission**: Calculated per process upon payment (managed via `Estado_Processos_Recebimento.xlsx`).
    - **Rules**: Business logic is driven by `config/Regras_Comissoes.xlsx`.
4.  **Output**: Generates `Comissoes_MM_AAAA.xlsx` and `Comissoes_Recebimento_MM_AAAA.xlsx`.

## 🛠 Developer Workflows
- **Run Calculation**:
  ```bash
  python calculo_comissoes.py --mes <MM> --ano <AAAA>
  ```
- **Generate Test Data**:
  ```bash
  python tests/geradores_dados/gerar_todos_dados_teste.py
  python tests/geradores_dados/gerar_rentabilidade_teste.py
  ```
- **Frontend Development**:
  - **UI**: `cd frontend && npm start` (React)
  - **Adapter**: `cd frontend/adapter && uvicorn app:app --reload` (FastAPI)
- **Testing**:
  - Use `pytest` for unit tests in `tests/`.
  - Refer to `documentacoes/guias/COMO_EXECUTAR_TESTES_EXPANDIDOS.md` for integration test scenarios.

## 📏 Conventions & Patterns
- **Compatibility**: `calculo_comissoes.py` contains "compatibility imports" to support the migration to `src/`. **Do not remove these** without verifying legacy dependencies.
- **Logging**: Use `self._log_validacao(level, msg, context)` or `ValidationLogger` for business logic validation. Avoid raw `print` for errors.
- **State Management**: `ProcessStateManager` (in `models/process_state.py`) handles the persistence of payment states. Do not manually edit `Estado_Processos_Recebimento.xlsx` via code; use the manager.
- **Currency**: Always use `src.currency.RateCalculator` for conversions. Do not hardcode exchange rates or fetch from external APIs directly in the calculation loop.

## 📂 Key Directories
- `auditoria_pdf/`: PDF generation logic (Orchestrator -> Data Collector -> Generator).
- `config/`: Configuration files (Rules, Goals).
- `dados_entrada/`: Input Excel files.
- `documentacoes/`: **Critical**. Check `documentacoes/guias/` for operational procedures before changing workflows.
- `frontend/`: React application and Python adapter.
- `src/`: New core modules (preferred for new logic).
