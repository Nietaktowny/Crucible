# Diagram

```mermaid
flowchart TD

Loader --> Preprocessor
Preprocessor --> Compiler
Compiler --> Optimizer
Optimizer --> Executor
Executor --> Polars
```